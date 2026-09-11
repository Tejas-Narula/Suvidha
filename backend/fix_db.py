from supabase import create_client
import json

url = "https://vmozwacurzfxmolucnxc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtb3p3YWN1cnpmeG1vbHVjbnhjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4OTEyOTI5OSwiZXhwIjoyMTA0NzA1Mjk5fQ.FfrHT3W8f7FD8Iy_NC-vx-v4yWxLhKxO7DpYMix7B18"
client = create_client(url, key)

response = client.table("government_schemas").select("*").ilike("service_title", "%Rail%").execute()

for row in response.data:
    print("ID:", row.get("id"))
    print("Title:", row.get("service_title"))
    print("Fields:", json.dumps(row.get("form_fields"), indent=2))
