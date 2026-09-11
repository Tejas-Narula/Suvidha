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
  const wsUrlBase = (import.meta as any).env.VITE_WS_URL || 'ws://localhost:8000/ws/browser/';
  ws = new WebSocket(`${wsUrlBase}${sessionId}`);

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

    const executeContentScript = (tabId: number) => {
      chrome.tabs.sendMessage(tabId, {
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
          sendBackendEvent('OTP_REQUIRED', { message: `Please ask the user for: ${res.field_name}` });
        } else if (res?.status === 'READY_FOR_SUBMISSION') {
          currentState = { ...currentState, status: 'READY_FOR_SUBMISSION' };
          broadcastState();
          sendBackendEvent('READY_FOR_SUBMISSION');
        }
      });
    };

    try {
      if (activeTabId) {
        executeContentScript(activeTabId);
      } else {
        const urlToOpen = target?.form_url || 'https://google.com';
        const tab = await chrome.tabs.create({ url: urlToOpen, active: true });
        activeTabId = tab.id!;
        
        setTimeout(() => {
          executeContentScript(activeTabId!);
        }, 4000); 
      }
    } catch (error: any) {
      console.error("Error creating tab:", error);
      currentState = { ...currentState, status: 'ERROR', error: error.toString() };
      broadcastState();
    }
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
