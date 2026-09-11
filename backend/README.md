# 🚀 Government Service Orchestrator (Backend)

Lightweight, high-performance FastAPI orchestration backend that bridges **Sarvam AI Voice Agents**, **Supabase pgvector Knowledge Base**, and the **Browser Automation Agent (Chrome Extension)**.

---

## 📋 Features

1. **Sarvam AI Voice Integration**:
   * `POST /api/submit`: Ingests speech-extracted citizen application fields, matches the civic service in pgvector, maps form fields dynamically, and initiates browser automation.
   * `GET /api/submit/{submission_id}/status`: Polling endpoint for voice agent during live phone calls.
   * Interactive corrections: handles missing information and OTP verification dynamically.

2. **Supabase pgvector Semantic Search**:
   * Generates 384-dimensional normalized vector embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
   * Queries Supabase `match_government_schemas` RPC for sub-millisecond similarity retrieval.

3. **Dynamic Field Mapping & Browser Dispatch**:
   * Intelligent alias resolution (e.g. `citizen_name` -> `#txtAadhaar` / `#txtName`, `phone` -> `#txtMobile`).
   * Dispatches structured execution payloads to `BROWSER_AGENT_API_URL` (with configurable mock variable support).

4. **Real-time WebSockets**:
   * `WS /ws/browser/{session_id}`: Bi-directional event stream with the Chrome Extension.
   * Intercepts `OTP_REQUIRED`, `OTP_COMPLETED`, `READY_FOR_SUBMISSION`, `SUBMISSION_SUCCESS`, `SUBMISSION_FAILED`.

---

## 🛠️ API Reference

### 1. Submit Application / Update Field
* **URL**: `POST /api/submit`
* **Headers**: `Authorization: Bearer <API_KEY>`
* **Request Body (Initial)**:
  ```json
  {
    "service_type": "farmer registration",
    "citizen_name": "Mukesh Kumar",
    "aadhaar_no": "123456789012",
    "mobile_no": "9876543210",
    "state": "Rajasthan",
    "rural_urban": "Rural"
  }
  ```
* **Response**:
  ```json
  {
    "submission_id": "SUB12F6B8A2",
    "status": "received"
  }
  ```

* **Request Body (Update / OTP Submission)**:
  ```json
  {
    "submission_id": "SUB12F6B8A2",
    "provided_field": "otp",
    "provided_value": "459102"
  }
  ```

---

### 2. Check Submission Status
* **URL**: `GET /api/submit/{submission_id}/status`
* **Headers**: `Authorization: Bearer <API_KEY>`
* **Response**:
  ```json
  {
    "status": "needs_correction",
    "message": "OTP required on government website",
    "field_with_issue": "otp"
  }
  ```

---

### 3. Session State Inspection
* **URL**: `GET /api/sessions/{session_id}/state`
* **Response**:
  ```json
  {
    "session_id": "sess_c4178f7409c4",
    "service_id": "PM-Kisan New Farmer Registration",
    "query": "Mukesh Kumar | 123456789012 | Rajasthan | farmer registration",
    "browser_connected": true,
    "voice_connected": true,
    "status": "in_progress",
    "current_step": null,
    "waiting_for_user": false,
    "user_action": null,
    "workflow": { ... },
    "matched_schema": { ... },
    "browser_payload": { ... }
  }
  ```

---

## ⚙️ Configuration (.env)

```env
# Supabase Configuration
SUPABASE_URL=https://vmozwacurzfxmolucnxc.supabase.co
SUPABASE_KEY=your-supabase-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Sarvam / Security
API_KEY=dev_secret_key

# Browser Agent API Endpoint & Mock Mode
BROWSER_AGENT_API_URL=http://localhost:8001/api/automate
BROWSER_AGENT_MOCK_MODE=true

# Session Expiry (in seconds)
SESSION_EXPIRE_SECONDS=3600
```

---

## 🏃 Running the Server

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger docs available at: `http://localhost:8000/docs`.
