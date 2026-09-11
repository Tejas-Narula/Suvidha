import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from app.config import settings
from app.models.session import ApplicationSession

logger = logging.getLogger(__name__)

class BrowserAgentService:
    """
    Browser Agent Dispatch & Field Mapping Service:
    - Dynamically maps citizen data from voice session into precise DOM selectors
    - Formats the complete structured automation JSON payload
    - Dispatches payload to the Browser Agent API (with MOCK VARIABLE support) & WebSocket
    """
    def __init__(self):
        self.api_url = settings.BROWSER_AGENT_API_URL
        self.mock_mode = settings.BROWSER_AGENT_MOCK_MODE

    def _resolve_field_value(self, field_def: Dict[str, Any], collected_data: Dict[str, Any]) -> Optional[Any]:
        """
        Dynamically matches a form field selector/name to extracted citizen data
        using semantic alias grouping and fuzzy matching.
        """
        field_name = (field_def.get("field_name") or "").lower().strip()
        css_selector = (field_def.get("css_selector") or "").lower().strip()
        input_type = (field_def.get("input_type") or "").lower().strip()

        # 1. Exact key match
        for k, v in collected_data.items():
            if k.lower() in [field_name, css_selector.replace("#", "").replace(".", "")]:
                return v

        # 2. Semantic Alias Groups
        aliases = {
            "name": ["full_name", "citizen_name", "name", "applicant_name", "first_name", "user_name", "citizen"],
            "mobile": ["mobile_no", "mobile_number", "mobile", "phone_number", "phone", "contact_no", "contact", "contact_number"],
            "aadhaar": ["aadhaar_no", "aadhaar_number", "aadhaar", "uid", "uid_no"],
            "address": ["ward_address", "address", "residential_address", "location", "landmark", "ward", "city"],
            "description": ["complaint_details", "description", "grievance_description", "grievance_text", "incident_description", "query", "issue", "problem"],
            "state": ["state", "state_name", "stName", "selState"],
            "district": ["district", "district_name", "selDistrict"],
            "dob": ["dob", "date_of_birth", "birth_date"],
            "pnr": ["pnr_no", "pnr", "pnr_uts"],
            "train": ["train_no", "train_number", "trainno"],
            "uan": ["uan_no", "uan", "pf_number"],
            "otp": ["otp", "regotp", "mobile_otp", "provided_value"]
        }

        # Check aliases against field_name and css_selector
        for category, candidate_keys in aliases.items():
            if category in field_name or category in css_selector:
                for ck in candidate_keys:
                    if ck in collected_data and collected_data[ck]:
                        return collected_data[ck]

        # 3. Fallback: match any key in collected_data that is a substring of field_name or vice-versa
        for k, v in collected_data.items():
            k_clean = k.lower().replace("_", "")
            fn_clean = field_name.replace(" ", "").replace("_", "")
            if (k_clean in fn_clean or fn_clean in k_clean) and v:
                return v

        # 4. Default dropdown option matching if options are present
        options = field_def.get("options") or []
        if options and input_type in ["dropdown", "select", "radio"]:
            # Check if any option matches collected values
            for opt in options:
                for val in collected_data.values():
                    if isinstance(val, str) and (val.lower() in opt.lower() or opt.lower() in val.lower()):
                        return opt.split(" ")[0] if "(" in opt else opt

        return None

    def build_browser_agent_payload(self, session: ApplicationSession) -> Dict[str, Any]:
        """
        Builds the complete, rich JSON payload for the Browser Automation Agent
        incorporating dynamic field mappings and workflow execution instructions.
        """
        schema = session.matched_schema or {}
        collected = session.collected_data or {}
        form_fields_raw = schema.get("form_fields") or []

        # Map dynamic form fields
        mapped_fields = []
        has_otp = False
        has_captcha = False
        otp_selector = None

        for f in form_fields_raw:
            field_name = f.get("field_name", "Field")
            input_type = f.get("input_type", "text").lower()
            selector = f.get("css_selector", "")
            is_req = f.get("is_required", False)
            
            # Resolve dynamic value from citizen data
            val = self._resolve_field_value(f, collected)

            # Detect action type
            action = "type"
            if input_type in ["dropdown", "select"]:
                action = "select_option"
            elif input_type in ["radio", "checkbox"]:
                action = "click"

            # Check for OTP / Captcha special fields
            if "otp" in field_name.lower() or "otp" in selector.lower() or input_type == "otp":
                has_otp = True
                otp_selector = selector
                val = collected.get("otp") or collected.get("provided_value") or ""
            
            if "captcha" in field_name.lower() or "captcha" in selector.lower() or input_type == "captcha":
                has_captcha = True

            mapped_fields.append({
                "field_name": field_name,
                "input_type": input_type,
                "selector": selector,
                "value": str(val) if val is not None else "",
                "action": action,
                "is_required": is_req
            })

        # Submission and interceptor configuration
        submit_btn = schema.get("submit_button_selector") or "button[type='submit']"
        
        payload = {
            "command": "FILL_AND_PREPARE_SUBMISSION",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session": {
                "session_id": session.session_id,
                "submission_id": session.submission_id or "",
                "service_title": schema.get("service_title") or session.service_id or "Civic Service",
                "department_name": schema.get("department_name") or "Government Portal"
            },
            "target": {
                "portal_url": schema.get("portal_url") or "",
                "form_url": schema.get("form_url") or ""
            },
            "navigation_flow": schema.get("navigation_steps") or [],
            "form_filling": {
                "mode": "sequential_fill",
                "fields": mapped_fields
            },
            "submission_config": {
                "submit_button_selector": submit_btn,
                "auto_submit": False,
                "otp_interceptor": {
                    "requires_otp": has_otp,
                    "otp_input_selector": otp_selector,
                    "otp_trigger_button": "#btnGetOtp" if has_otp else None,
                    "otp_verify_button": "#btnVerifyOtp" if has_otp else None
                },
                "captcha_interceptor": {
                    "requires_captcha": has_captcha,
                    "captcha_selector": "#txtCaptcha" if has_captcha else None
                }
            },
            "submission_steps": schema.get("submission_steps") or []
        }

        return payload

    async def dispatch_to_browser_agent(self, session: ApplicationSession) -> Dict[str, Any]:
        """
        Assembles dynamic payload and calls the Browser Agent API (with MOCK VARIABLE fallback)
        and sends to connected WebSocket extensions.
        """
        payload = self.build_browser_agent_payload(session)
        session.browser_payload = payload

        # Broadcast payload over active WebSocket if extension is connected
        from app.websocket.browser import manager
        try:
            await manager.send_command(session.session_id, payload)
            logger.info(f"Broadcasted automation command over WebSocket for session: {session.session_id}")
        except Exception as e:
            logger.debug(f"WebSocket broadcast notice (no client connected yet): {e}")

        # Call Browser Agent API endpoint
        logger.info(f"Dispatching payload to Browser Agent API: {self.api_url} (MockMode: {self.mock_mode})")
        
        if self.mock_mode:
            # Simulated Browser Agent API Response (Mock Variable)
            mock_response = {
                "status": "dispatched",
                "endpoint": self.api_url,
                "agent_job_id": f"job_mock_{session.session_id[:8]}",
                "target_form_url": payload["target"]["form_url"],
                "fields_count": len(payload["form_filling"]["fields"]),
                "fields_with_values": len([f for f in payload["form_filling"]["fields"] if f.get("value")]),
                "dispatched_at": datetime.utcnow().isoformat() + "Z",
                "message": "Browser automation payload generated and dispatched successfully."
            }
            session.browser_agent_response = mock_response
            logger.info(f"✅ Browser Agent Mock API Response: {json.dumps(mock_response, indent=2)}")
            return mock_response

        # Live HTTP POST to real Browser Agent endpoint if configured
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.api_url, json=payload)
                data = resp.json() if resp.status_code == 200 else {"status": "error", "code": resp.status_code}
                session.browser_agent_response = data
                return data
        except Exception as e:
            logger.warning(f"Browser agent HTTP dispatch notice: {e}")
            fallback_resp = {"status": "queued_offline", "error": str(e)}
            session.browser_agent_response = fallback_resp
            return fallback_resp

browser_agent_service = BrowserAgentService()
