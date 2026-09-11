from supabase import create_client
import json

url = "https://vmozwacurzfxmolucnxc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtb3p3YWN1cnpmeG1vbHVjbnhjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTEyOTI5OSwiZXhwIjoyMTA0NzA1Mjk5fQ.FfrHT3W8f7FD8Iy_NC-vx-v4yWxLhKxO7DpYMix7B18"
client = create_client(url, key)

new_fields = [
  {
    "options": [],
    "field_name": "Mobile No.",
    "input_type": "text",
    "is_required": True,
    "placeholder": "",
    "css_selector": "#contact_no"
  },
  {
    "options": [],
    "field_name": "OTP",
    "input_type": "otp",
    "is_required": True,
    "placeholder": "OTP",
    "css_selector": "#regotp"
  },
  {
    "options": [
      "PNR",
      "UTS"
    ],
    "field_name": "Journey Details",
    "input_type": "dropdown",
    "is_required": True,
    "placeholder": "",
    "css_selector": "#pmode"
  },
  {
    "options": [],
    "field_name": "UTS No*",
    "input_type": "text",
    "is_required": False,
    "placeholder": "",
    "css_selector": "#uts_no"
  },
  {
    "options": [],
    "field_name": "PNR No*",
    "input_type": "text",
    "is_required": True,
    "placeholder": "",
    "css_selector": "#pnr_uts"
  },
  {
    "options": [],
    "field_name": "Train Number*",
    "input_type": "text",
    "is_required": False,
    "placeholder": "",
    "css_selector": "#train_no"
  },
  {
    "options": [],
    "field_name": "Grievance/Assistance Description*",
    "input_type": "textarea",
    "is_required": True,
    "placeholder": "Enter Description...",
    "css_selector": "#complaint_desc"
  }
]

response = client.table("government_schemas").update({
    "form_fields": new_fields
}).eq("id", "8734f504-d079-42e5-bfd3-3e91507ff402").execute()

print("DB Updated Successfully!")
