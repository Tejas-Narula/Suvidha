# 🏛️ Suvidha (सुविधा)

> **Autonomous AI Voice-to-Browser Government Service Orchestrator**  
> Bridging **Sarvam AI Voice Agents**, **Supabase pgvector Knowledge Base**, and **Browser Automation Agents** to simplify civic services and government form filings for every citizen.

---

## 🌟 System Overview

**Suvidha** enables citizens to interact with complex Indian government portals using natural voice in their native language. While the citizen speaks with the **Sarvam AI Voice Agent**, the backend:
1. Extracts the citizen's civic query and intent.
2. Performs **384-dimensional semantic similarity vector search** (`all-MiniLM-L6-v2`) over indexed government form blueprints in **Supabase pgvector**.
3. Dynamically maps citizen data into target DOM form fields and selectors.
4. Dispatches the structured automation payload to the **Browser Automation Agent (Chrome Extension)** to fill the form, handle OTP/captcha flows, and execute the final submission upon user confirmation.

---

## 🏗️ Architecture Diagram

```
                              ┌────────────────────────────────────────┐
                              │         Sarvam AI Voice Agent          │
                              │    (Citizen Natural Voice Call)        │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  │ 1. POST /api/submit
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FastAPI Backend (backend/)                                  │
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ • API Gateway: Sarvam submission, status polling & session state                    │   │
│   │ • Vector Search Service: 384-d query embedding & match_government_schemas RPC       │   │
│   │ • Dynamic Field Mapper: Maps citizen data -> CSS input selectors & actions          │   │
│   │ • Session Manager: Thread-safe in-memory session state & status tracking            │   │
│   │ • Browser Agent Client: Dispatches structured JSON to Browser Agent API & WebSocket │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────────┬───────────────┘
                                │                                             │
                                │ Query & Retrieval                           │ 4. Automation JSON
                                ▼                                             ▼
     ┌──────────────────────────────────────┐             ┌───────────────────────────────────┐
     │      Supabase Vector DB (pgvector)   │             │   Browser Agent / Chrome Ext.     │
     │                                      │             │                                   │
     │  • government_schemas table          │             │  • Step-by-step DOM navigation    │
     │  • 384-dim HNSW Cosine Index         │             │  • Sequential field typing        │
     │  • match_government_schemas RPC      │             │  • OTP / Captcha Interceptor      │
     │  • Form blueprints & CSS selectors   │             │  • Final submission confirmation  │
     └──────────────────▲───────────────────┘             └───────────────────────────────────┘
                        │
                        │ 0. Crawl, Parse & Index
     ┌──────────────────┴───────────────────────────────────────────────────┐
     │                Autonomous Scraping Pipeline (parsing/)               │
     │                                                                      │
     │  • Playwright + BeautifulSoup: Dynamic DOM rendering & sanitization  │
     │  • Groq LLM Extractor: Form fields, CSS selectors & step synthesis   │
     │  • HuggingFace Embedder: 384-dim normalized vector generation        │
     └──────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Repository Structure

```
Suvidha/
├── backend/                        # Real-time FastAPI Orchestration Backend
│   ├── app/
│   │   ├── api/                    # REST API Endpoints (Sarvam, Sessions, Health)
│   │   │   ├── sarvam.py           # /api/submit & status checking
│   │   │   ├── sessions.py         # Session management & state inspection
│   │   │   └── health.py           # Healthcheck
│   │   ├── models/                 # Pydantic data models (ApplicationSession)
│   │   ├── schemas/                # Request/Response validation schemas
│   │   ├── services/               # Core business services
│   │   │   ├── session_manager.py  # Thread-safe session storage
│   │   │   ├── embedding_service.py# 384-d HuggingFace vector embedder
│   │   │   ├── vector_service.py   # Supabase pgvector RPC search
│   │   │   └── browser_agent.py    # Dynamic field mapping & Browser Agent dispatcher
│   │   ├── websocket/              # WebSocket hubs for Chrome Extension
│   │   │   └── browser.py          # /ws/browser/{session_id}
│   │   └── config.py               # Settings & environment variables
│   ├── requirements.txt            # Backend Python dependencies
│   └── README.md                   # Backend detailed documentation
│
├── parsing/                        # Autonomous Portal Scraping & Knowledge Ingestion
│   ├── src/
│   │   ├── scraper.py              # Playwright & BeautifulSoup DOM extractor
│   │   ├── extractor.py            # Groq LLM structured blueprint parser
│   │   ├── embeddings.py           # all-MiniLM-L6-v2 384-d vector embeddings
│   │   └── db.py                   # Supabase pgvector upsert & RPC query client
│   ├── models/                     # Local model weights directory (optional)
│   ├── schema.sql                  # PostgreSQL & pgvector schema definitions
│   ├── schema_router_crawler.py    # CLI crawler and testing tool
│   ├── requirements.txt            # Parsing pipeline dependencies
│   └── README.md                   # Parsing module documentation
│
└── README.md                       # Main project documentation
```

---

## ⚡ End-to-End Execution Flow

### 1. Citizen Submission (`POST /api/submit`)
The voice agent sends extracted details from the citizen:
```json
POST /api/submit
Authorization: Bearer dev_secret_key
Content-Type: application/json

{
  "service_type": "farmer registration",
  "citizen_name": "Mukesh Kumar",
  "aadhaar_no": "123456789012",
  "mobile_no": "9876543210",
  "state": "Rajasthan",
  "rural_urban": "Rural"
}
```

### 2. Semantic Search & Blueprint Retrieval
1. `vector_service.extract_query_text()` synthesizes the search query: `"Mukesh Kumar | 123456789012 | Rajasthan | farmer registration"`.
2. `embedder.embed_query()` computes a 384-dimensional vector.
3. Supabase RPC `match_government_schemas` matches `PM-Kisan New Farmer Registration` (`https://pmkisan.gov.in/RegistrationFormNew.aspx`).

### 3. Dynamic Field Mapping & Browser Dispatch
`browser_agent_service` maps citizen values directly to DOM selectors:
* `Aadhaar Number` -> `#txtAadhaar` with value `"123456789012"`
* `Mobile Number` -> `#txtMobile` with value `"9876543210"`
* `State` -> `#selState` with value `"Rajasthan"`
* `Submit Button` -> `#btnGetOtp`

Payload is dispatched to `BROWSER_AGENT_API_URL` and broadcasted to connected Chrome extensions via WebSocket.

### 4. Interactive Human-in-the-Loop (OTP & Captcha)
* If the portal requests an OTP, the extension sends `OTP_REQUIRED` over WebSocket.
* The session status changes to `needs_correction` (`field_with_issue = "otp"`).
* The voice agent asks the citizen for the OTP, and calls `POST /api/submit` with `submission_id` and `provided_value: "459102"`.
* The automation immediately resumes.

---

## 🚀 Quickstart Guide

### Prerequisites
* Python 3.11+
* Supabase Account (with pgvector enabled)
* Groq API Key (for parsing & blueprint extraction)

### 1. Database Setup
1. In your Supabase SQL Editor, execute [`parsing/schema.sql`](file:///c:/Users/Aryan%20Sharma/Desktop/Suvidha/parsing/schema.sql).
2. This creates the `government_schemas` table, the HNSW cosine vector index, and the `match_government_schemas` search function.

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```
Configure `backend/.env` (or rely on defaults):
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
API_KEY=dev_secret_key
BROWSER_AGENT_API_URL=http://localhost:8001/api/automate
BROWSER_AGENT_MOCK_MODE=true
```
Run backend server:
```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Parsing & Ingestion Setup
```bash
cd parsing
pip install -r requirements.txt
playwright install chromium
```
Configure `parsing/.env`:
```env
GROQ_API_KEY=your-groq-api-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```
Run Crawler / Self-Test:
```bash
python schema_router_crawler.py --test
python schema_router_crawler.py --query "lodge streetlight complaint"
```

---

## 🔒 Security & Privacy
* No citizen data is permanently stored in the scraper database—only generic portal DOM blueprints.
* Session data in backend is in-memory and transient with auto-expiration (`SESSION_EXPIRE_SECONDS: 3600`).
* Bearer API authentication protects all Sarvam AI integration endpoints.
