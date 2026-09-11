# Suvidha Browser Automation (Step 2)

This directory contains the self-contained Browser Agent API and the Chrome Extension for deterministic browser automation.

## 1. Installation
Ensure you have Node.js and Docker installed.

```bash
cd extension
npm install
```

## 2. Environment Variables (.env)
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Default configuration:
- `BROWSER_AGENT_PORT=8000`
- `MAIN_API_URL=http://host.docker.internal:8000`

## 3. Docker Startup
Start the Browser Agent API using Docker:
```bash
docker compose up --build -d
```
The API will be available at `http://localhost:8000`.

## 4. Extension Build
Build the Chrome extension (React Side Panel + Service Worker + Content Script):
```bash
npm run build
```
This generates the extension files in the `dist/` directory.

## 5. Chrome Installation
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer Mode**.
3. Click **Load unpacked** and select the `extension/dist` directory.
The extension will automatically connect to `ws://localhost:8000` when a process is assigned.

## 6. API Endpoint Documentation
- `POST /v1/automations`: Starts an automation (receives `START_AUTOMATION` intent).
- `GET /v1/automations/{process_id}`: Retrieves process state.
- `GET /v1/automations/{process_id}/events`: Retrieves event logs.
- `POST /v1/automations/{process_id}/input`: Submit manual user input.
- `POST /v1/automations/{process_id}/auth-complete`: Indicate manual auth completion.
- `POST /v1/automations/{process_id}/confirm`: Confirm final submission.
- `POST /v1/extensions/register`: Internal endpoint for extension registration.
- `POST /v1/integrations/start`: Same as `/v1/automations`, used by Main API.

## 7. START_AUTOMATION Schema
```json
{
  "event": "START_AUTOMATION",
  "timestamp": "2026-09-12T00:30:00Z",
  "session": { "session_id": "...", "submission_id": "...", "service_title": "...", "department": "..." },
  "target": { "portal_url": "...", "form_url": "..." },
  "navigation_flow": [ { "step_number": 1, "action": "navigate", "target_url": "..." } ],
  "form_filling": { "mode": "auto_fill", "fields": [ ... ] },
  "submission_config": { ... },
  "instructions": [ ... ]
}
```

## 8. Process Lifecycle
`CREATED` → `STARTING` → `RUNNING` → (`WAITING_FOR_USER` | `WAITING_FOR_AUTH`) → `RUNNING` → `WAITING_FOR_CONFIRMATION` → `COMPLETED` | `FAILED`

## 9. WebSocket Protocol
- Connected dynamically at `ws://localhost:8000/v1/ws/{process_id}`
- **Server -> Extension Commands:** `OPEN_TAB`, `NAVIGATE`, `CLICK_SELECTOR`, `FILL_FIELD`, `SELECT_OPTION`, `USER_INPUT_PROVIDED`, `CONFIRM_SUBMISSION`, `AUTH_COMPLETED_BY_USER`.
- **Extension -> Server Events:** `TAB_CREATED`, `ACTION_COMPLETED`, `ACTION_FAILED`.

## 10. Main API Integration Example
```bash
curl -X POST http://localhost:8000/v1/integrations/start \
  -H "Content-Type: application/json" \
  -d @test/start_automation.json
```

## 11. User Input Flow
When a field is missing, the extension enters `WAITING_FOR_USER`. The Side Panel displays the question, and the user submits the value, which posts to `/v1/automations/{process_id}/input`.

## 12. OTP / Auth Flow
When OTP inputs are detected based on `submission_config`, the state becomes `WAITING_FOR_AUTH`. The user completes OTP in the active tab, then clicks "I have completed it" in the side panel.

## 13. Submission Confirmation
Before clicking the final submit button, the state shifts to `WAITING_FOR_CONFIRMATION`. The Side Panel prompts the user to either Confirm or Cancel.

## 14. Complete Local E2E Test
1. Start the API: `docker compose up --build -d`
2. Start the mock portal: `node test/mock-portal/server.js` (runs on 9000)
3. Load extension into Chrome and ensure the service worker registers.
4. Run: `curl -X POST http://localhost:8000/v1/automations -H "Content-Type: application/json" -d @test/start_automation.json`
5. Observe the automated sequence in Chrome.
