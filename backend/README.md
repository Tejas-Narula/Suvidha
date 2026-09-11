# Government Service Orchestrator

This is a lightweight Python FastAPI backend that serves as the real-time orchestration layer between:
1. Sarvam AI Voice Agent
2. Supabase pgvector DB (Government Workflows)
3. Chrome Extension (Browser Automation)

## Requirements
- Python 3.11+
- FastAPI
- Supabase

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up `.env` from `.env.example`.
3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Sarvam Integration
- `POST /api/submit`: Submission endpoint called by the voice agent with all collected fields.
- `GET /api/submit/{submission_id}/status`: Status polling endpoint for the voice agent.

### WebSockets
- `WS /ws/browser/{session_id}`: Realtime connection for the Chrome extension to report events (`OTP_REQUIRED`, `SUBMISSION_SUCCESS`) and receive commands.

## Architecture
- `app/api/`: REST APIs for Sarvam and session management
- `app/websocket/`: WebSocket endpoints
- `app/services/`: Core logic (SessionManager, VectorService)
