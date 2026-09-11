import os
import re
import json
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from groq import AsyncGroq

logger = logging.getLogger(__name__)

# ==============================================================================
# Pydantic Schemas for Government Form Blueprints
# ==============================================================================

class FormField(BaseModel):
    field_name: str = Field(description="Label or name of the field (e.g., 'Aadhaar Number', 'Grievance Description', 'District')")
    input_type: str = Field(description="Category: text, dropdown, file, radio, checkbox, date, number, textarea, otp, captcha")
    css_selector: str = Field(description="Precise CSS selector to interact with this input element (e.g., '#txtAadhaar', 'select[name=district]', 'textarea#desc')")
    is_required: bool = Field(default=False, description="True if mandatory to submit the form")
    placeholder: Optional[str] = Field(default="", description="Placeholder text inside the input")
    options: List[str] = Field(default_factory=list, description="Dropdown or radio options if applicable")


class NavigationStep(BaseModel):
    step_number: int = Field(description="Step sequence number (1, 2, 3...)")
    action_description: str = Field(description="Description of what to click (e.g., 'Click on Citizen Services -> Register Grievance')")
    element_selector: str = Field(description="CSS selector or URL for this navigation step")


class GovernmentServiceBlueprint(BaseModel):
    service_title: str = Field(description="Official name of the service (e.g., 'Sanitation & Garbage Disposal Complaint')")
    intent: str = Field(description="What civic issue or service this form handles (e.g., 'Report uncollected garbage, open drains, water leakage')")
    department_name: str = Field(description="Government department or municipal body handling this form")
    portal_url: str = Field(description="Base portal URL")
    form_url: str = Field(description="Direct URL where the form resides")
    navigation_steps: List[NavigationStep] = Field(default_factory=list, description="Sequence of clicks to reach the form from the homepage")
    form_fields: List[FormField] = Field(default_factory=list, description="All interactable form input fields")
    submit_button_selector: str = Field(description="Precise CSS selector for the primary submit/proceed button (e.g., '#btnSubmit', 'input[type=submit]')")
    submission_steps: List[str] = Field(default_factory=list, description="Step-by-step instructions to fill and submit the form")
    search_content: Optional[str] = Field(default=None, description="Rich textual representation used for generating vector embeddings in pgvector")


# ==============================================================================
# Groq LLM Extractor
# ==============================================================================

def _normalize_dict_keys(d: Any) -> Any:
    """Normalizes camelCase keys to snake_case keys recursively."""
    if isinstance(d, list):
        return [_normalize_dict_keys(item) for item in d]
    elif isinstance(d, dict):
        new_d = {}
        for k, v in d.items():
            snake_k = re.sub(r'(?<!^)(?=[A-Z])', '_', k).lower()
            new_d[snake_k] = _normalize_dict_keys(v)
        return new_d
    return d


class GroqServiceExtractor:
    """
    Extracts structured government service workflows, interactive form fields,
    CSS selectors, and submission instructions using Groq LLM.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "openai/gpt-oss-120b"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set. Please provide it in .env or constructor.")
        
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = model

    async def extract_service_blueprint(
        self,
        portal_url: str,
        form_url: str,
        dom_data: Dict[str, Any]
    ) -> GovernmentServiceBlueprint:
        """
        Takes sanitized DOM elements from BeautifulSoup and uses Groq to synthesize
        a complete GovernmentServiceBlueprint ready for pgvector indexing.
        """
        schema_json = json.dumps(GovernmentServiceBlueprint.model_json_schema(), indent=2)

        system_prompt = (
            "You are an expert web scraping and form automation parser for government portals. "
            "Your task is to analyze scraped HTML DOM data and output a structured JSON blueprint matching EXACTLY this JSON schema:\n\n"
            f"{schema_json}\n\n"
            "Key instructions:\n"
            "1. Use snake_case keys (service_title, intent, department_name, portal_url, form_url, navigation_steps, form_fields, submit_button_selector, submission_steps, search_content).\n"
            "2. Identify interactable input fields with accurate CSS selectors, types, and required status.\n"
            "3. Identify the exact CSS selector for the final submit button.\n"
            "4. Provide a clear list of submission_steps describing how to fill and submit the form.\n"
            "Respond ONLY with a valid JSON object."
        )

        user_content = (
            f"Portal URL: {portal_url}\n"
            f"Form URL: {form_url}\n"
            f"Page Headings: {json.dumps(dom_data.get('headings', []))}\n"
            f"Page Instructions/Text: {dom_data.get('instruction_text', '')[:1500]}\n"
            f"Form Fields Detected: {json.dumps(dom_data.get('form_elements', []), indent=2)}\n"
            f"Action/Submit Buttons Detected: {json.dumps(dom_data.get('action_buttons', []), indent=2)}\n\n"
            "Generate the complete GovernmentServiceBlueprint in valid JSON format."
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )

        raw_json_str = response.choices[0].message.content
        data = json.loads(raw_json_str)
        data = _normalize_dict_keys(data)

        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        if "portal_url" not in data or not data["portal_url"]:
            data["portal_url"] = portal_url
        if "form_url" not in data or not data["form_url"]:
            data["form_url"] = form_url

        blueprint = GovernmentServiceBlueprint(**data)

        # Build composite search content for vector embedding if not present
        if not blueprint.search_content:
            fields_summary = ", ".join([f.field_name for f in blueprint.form_fields])
            steps_summary = " ".join(blueprint.submission_steps)
            blueprint.search_content = (
                f"Service: {blueprint.service_title}\n"
                f"Department: {blueprint.department_name}\n"
                f"Intent: {blueprint.intent}\n"
                f"Form URL: {blueprint.form_url}\n"
                f"Fields: {fields_summary}\n"
                f"Submission Steps: {steps_summary}"
            )

        return blueprint
