import logging
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
from app.config import settings
from app.services.embedding_service import embedder

logger = logging.getLogger(__name__)

class VectorService:
    """
    Service to perform semantic search over Government Schemas stored in Supabase pgvector
    using 384-dimensional Hugging Face vector embeddings.
    """
    def __init__(self):
        self.client: Optional[Client] = None
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Supabase pgvector client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")

    def extract_query_text(self, data: Dict[str, Any], service_type: Optional[str] = None) -> str:
        """
        Extracts and synthesizes the citizen's civic query/intent from incoming data payload.
        """
        # Priority direct fields
        query_candidates = [
            data.get("query"),
            data.get("user_query"),
            data.get("complaint_details"),
            data.get("description"),
            data.get("grievance"),
            data.get("issue"),
            data.get("problem_description"),
            data.get("service_type") or service_type,
            data.get("department")
        ]
        
        # Filter non-empty strings
        found_parts = [str(c).strip() for c in query_candidates if c and str(c).strip()]
        
        if found_parts:
            return " | ".join(dict.fromkeys(found_parts)) # deduplicated in order
            
        # Fallback: concatenate descriptive string values from collected_data
        fallback_parts = []
        for k, v in data.items():
            if isinstance(v, str) and len(v.strip()) > 3:
                # ignore ids/tokens
                if not any(token in k.lower() for token in ["id", "token", "key", "password", "secret", "auth", "session"]):
                    fallback_parts.append(f"{k}: {v.strip()}")
                    
        return " | ".join(fallback_parts) if fallback_parts else "civic government service request"

    async def search_service(
        self,
        query: str,
        match_threshold: float = 0.25,
        match_count: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Performs semantic vector similarity search on Supabase pgvector using match_government_schemas RPC.
        Returns the highest-scoring matching government form schema & workflow.
        """
        if not query or not query.strip():
            return None

        # 1. Generate 384-dimensional vector embedding
        query_embedding = embedder.embed_query(query)

        # 2. Query Supabase pgvector if client is configured
        if self.client:
            try:
                rpc_params = {
                    "query_embedding": query_embedding,
                    "match_threshold": match_threshold,
                    "match_count": match_count
                }
                response = self.client.rpc("match_government_schemas", rpc_params).execute()
                matches = response.data or []
                
                if matches:
                    top_match = matches[0]
                    logger.info(
                        f"Found pgvector match for query '{query}': "
                        f"{top_match.get('service_title')} (similarity: {top_match.get('similarity', 0):.3f})"
                    )
                    return top_match
                else:
                    logger.info(f"No pgvector matches above threshold {match_threshold} for query: '{query}'")
            except Exception as e:
                logger.warning(f"Error querying Supabase match_government_schemas RPC: {e}")

        # 3. Graceful Fallback / Offline Mock for local testing & resilience
        query_lower = query.lower()
        if "streetlight" in query_lower or "light" in query_lower or "electricity" in query_lower:
            return {
                "service_title": "Streetlight Grievance & Outage Registration",
                "intent": "Report broken, damaged, or non-functioning streetlights",
                "department_name": "Municipal Corporation - Electrical Division",
                "portal_url": "https://services.jaipurmc.org",
                "form_url": "https://services.jaipurmc.org/complaints/new",
                "navigation_steps": [
                    {"step_number": 1, "action_description": "Open Civic Portal", "element_selector": "https://services.jaipurmc.org"},
                    {"step_number": 2, "action_description": "Click Register Grievance", "element_selector": "#btnGrievance"}
                ],
                "form_fields": [
                    {"field_name": "Full Name", "input_type": "text", "css_selector": "#txtName", "is_required": True},
                    {"field_name": "Mobile Number", "input_type": "text", "css_selector": "#txtMobile", "is_required": True},
                    {"field_name": "Department", "input_type": "dropdown", "css_selector": "select[name='department']", "is_required": True},
                    {"field_name": "Ward Address", "input_type": "textarea", "css_selector": "#txtAddress", "is_required": False}
                ],
                "submit_button_selector": "#btnSubmitGrievance",
                "submission_steps": [
                    "Fill citizen full name and 10-digit mobile number",
                    "Select Electricity / Streetlight department from dropdown",
                    "Provide ward and landmark address",
                    "Click submit button and await verification SMS"
                ],
                "similarity": 0.95
            }

        if "aadhaar" in query_lower:
            return {
                "service_title": "Aadhaar Address Update Service",
                "intent": "Update residential address in Aadhaar card online",
                "department_name": "Unique Identification Authority of India (UIDAI)",
                "portal_url": "https://myaadhaar.uidai.gov.in/",
                "form_url": "https://myaadhaar.uidai.gov.in/update-address",
                "navigation_steps": [
                    {"step_number": 1, "action_description": "Open myAadhaar Portal", "element_selector": "https://myaadhaar.uidai.gov.in/"},
                    {"step_number": 2, "action_description": "Login with OTP", "element_selector": "#btnLoginWithOtp"}
                ],
                "form_fields": [
                    {"field_name": "Aadhaar Number", "input_type": "text", "css_selector": "#txtAadhaar", "is_required": True},
                    {"field_name": "Captcha", "input_type": "text", "css_selector": "#txtCaptcha", "is_required": True},
                    {"field_name": "New Address", "input_type": "textarea", "css_selector": "#txtNewAddress", "is_required": True}
                ],
                "submit_button_selector": "#btnProceedToUpdate",
                "submission_steps": ["Enter Aadhaar number and OTP", "Enter new residential address", "Upload proof of address", "Submit application"],
                "similarity": 0.92
            }

        if "water" in query_lower or "sewer" in query_lower or "drain" in query_lower or "sanitation" in query_lower or "garbage" in query_lower:
            return {
                "service_title": "Sanitation & Water Supply Grievance",
                "intent": "Report sewage overflow, water leakage, or uncollected municipal waste",
                "department_name": "Public Health & Sanitation Department",
                "portal_url": "https://citizen.mpenagarpalika.gov.in",
                "form_url": "https://citizen.mpenagarpalika.gov.in/pgportal/register-complaint",
                "navigation_steps": [
                    {"step_number": 1, "action_description": "Open eNagarPalika Portal", "element_selector": "https://citizen.mpenagarpalika.gov.in"}
                ],
                "form_fields": [
                    {"field_name": "Citizen Name", "input_type": "text", "css_selector": "#citizen_name", "is_required": True},
                    {"field_name": "Mobile", "input_type": "text", "css_selector": "#mobile_no", "is_required": True},
                    {"field_name": "Complaint Category", "input_type": "dropdown", "css_selector": "#category", "is_required": True},
                    {"field_name": "Description", "input_type": "textarea", "css_selector": "#description", "is_required": True}
                ],
                "submit_button_selector": "button[type='submit']",
                "submission_steps": ["Select complaint category", "Enter contact details and description", "Click submit"],
                "similarity": 0.88
            }

        return None

vector_service = VectorService()
