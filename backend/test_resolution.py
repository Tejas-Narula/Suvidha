from app.services.browser_agent import browser_agent_service

collected = {"Mobile No.": "9876543210", "provided_field": "Mobile No.", "provided_value": "9876543210"}
field_def = {
    "field_name": "Mobile No.",
    "css_selector": "input[placeholder='Mobile No.']",
    "input_type": "text"
}

val = browser_agent_service._resolve_field_value(field_def, collected)
print("RESOLVED VALUE:", val)
