let ws: WebSocket | null = null;
let activeTabId: number | null = null;
let currentState: any = { status: 'DISCONNECTED', session_id: '' };
let currentSessionId: string | null = null;

// Allow the side panel to open when the extension icon is clicked
if (chrome.sidePanel && chrome.sidePanel.setPanelBehavior) {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch((error) => console.error(error));
}

function connectWebSocket(sessionId: string) {
  if (ws) ws.close();
  ws = new WebSocket(`wss://suvidha-g37k.onrender.com/ws/browser/${sessionId}`);

  ws.onopen = () => {
    console.log('WebSocket connected for session:', sessionId);
    currentState = { status: 'WAITING_FOR_PROCESS', session_id: sessionId };
    broadcastState();
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleCommand(data);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    currentState = { status: 'DISCONNECTED', session_id: '' };
    broadcastState();
    ws = null;
  };
}

async function handleCommand(commandData: any) {
  const { command, session, target, form_filling, submission_config } = commandData;

  const sendBackendEvent = (type: string, payloadData: any = {}) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type,
        payload: payloadData
      }));
    }
  };

  if (command === 'FILL_AND_PREPARE_SUBMISSION') {
    currentState = { status: 'RUNNING', session_id: currentSessionId, service_title: session?.service_title };
    broadcastState();

    // 1. Open the target form URL
    const tab = await chrome.tabs.create({ url: target.form_url, active: true });
    activeTabId = tab.id!;
    
    // 2. Wait for page load (simplistic)
    setTimeout(() => {
      // 3. Inject content script to execute form filling
      chrome.tabs.sendMessage(activeTabId!, {
        command: 'EXECUTE_FORM_FILL',
        fields: form_filling.fields,
        submission_config: submission_config
      }, (res) => {
        if (res?.status === 'OTP_REQUIRED') {
          currentState = { ...currentState, status: 'OTP_REQUIRED' };
          broadcastState();
          sendBackendEvent('OTP_REQUIRED', { message: 'OTP required on government website' });
        } else if (res?.status === 'FIELD_REQUIRED') {
          currentState = { ...currentState, status: 'FIELD_REQUIRED', missing_field: res.field_name };
          broadcastState();
          // Send event formatted as OTP_REQUIRED to use existing backend logic for missing fields
          sendBackendEvent('OTP_REQUIRED', { message: `Please ask the user for: ${res.field_name}` });
        } else if (res?.status === 'READY_FOR_SUBMISSION') {
          currentState = { ...currentState, status: 'READY_FOR_SUBMISSION' };
          broadcastState();
          sendBackendEvent('READY_FOR_SUBMISSION');
        }
      });
    }, 4000); 
  }
}

function broadcastState() {
  chrome.runtime.sendMessage({ type: 'STATE_UPDATE', payload: currentState }).catch(() => {});
}

// Sidepanel requests state
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'GET_STATE') {
    sendResponse(currentState);
  } else if (message.type === 'CONNECT_SESSION') {
    currentSessionId = message.session_id;
    connectWebSocket(message.session_id);
    sendResponse({ success: true });
  }
});
