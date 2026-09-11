let ws: WebSocket | null = null;
let activeTabId: number | null = null;
let currentState: any = { status: 'WAITING_FOR_PROCESS' };
let extensionId = "ext_" + Math.random().toString(36).substr(2, 9);
let currentProcessId: string | null = null;

async function registerExtension() {
  try {
    const res = await fetch('http://localhost:8000/v1/extensions/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        extension_id: extensionId,
        browser_session_id: "session_1",
        status: "ONLINE"
      })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.assigned_process_id && data.assigned_process_id !== currentProcessId) {
        currentProcessId = data.assigned_process_id;
        connectWebSocket(currentProcessId!);
      }
    }
  } catch (e) {
    console.log("Failed to register with Browser Agent API", e);
  }
}

// Periodically register
setInterval(registerExtension, 3000);
registerExtension();

function connectWebSocket(processId: string) {
  if (ws) ws.close();
  ws = new WebSocket(`ws://localhost:8000/v1/ws/${processId}`);

  ws.onopen = () => {
    console.log('WebSocket connected for process:', processId);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleCommand(data);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    ws = null;
  };
}

async function handleCommand(commandData: any) {
  const { command_id, command, payload } = commandData;

  const sendResponse = (event: string, additionalPayload: any = {}) => {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        event,
        command_id,
        payload: additionalPayload
      }));
    }
  };

  if (command === 'OPEN_TAB') {
    currentState = { status: 'STARTING', process_id: currentProcessId };
    broadcastState();

    const tab = await chrome.tabs.create({ url: payload.url, active: true });
    activeTabId = tab.id!;
    
    // Simplistic wait for now
    setTimeout(() => {
      sendResponse('TAB_CREATED', { tab_id: tab.id, url: tab.url });
    }, 2000); 
  } 
  else if (command === 'NAVIGATE') {
    if (!activeTabId) return;
    await chrome.tabs.update(activeTabId, { url: payload.url });
    setTimeout(() => {
      sendResponse('ACTION_COMPLETED');
    }, 2000);
  }
  else if (command === 'CLICK_SELECTOR') {
    if (!activeTabId) return;
    chrome.tabs.sendMessage(activeTabId, {
      command: 'CLICK_SELECTOR',
      selector: payload.selector
    }, (res) => {
      if (res?.status === 'ACTION_COMPLETED') {
        sendResponse('ACTION_COMPLETED');
      } else {
        sendResponse('ACTION_FAILED', { reason: res?.reason || 'UNKNOWN' });
      }
    });
  }
  else if (command === 'FILL_FIELD') {
    if (!activeTabId) return;
    chrome.tabs.sendMessage(activeTabId, {
      command: 'FILL_FIELD',
      selector: payload.selector,
      value: payload.value
    }, (res) => {
      if (res?.status === 'ACTION_COMPLETED') {
        sendResponse('ACTION_COMPLETED');
      } else {
        sendResponse('ACTION_FAILED', { reason: res?.reason || 'UNKNOWN' });
      }
    });
  }
  else if (command === 'SELECT_OPTION') {
    if (!activeTabId) return;
    chrome.tabs.sendMessage(activeTabId, {
      command: 'SELECT_OPTION',
      selector: payload.selector,
      value: payload.value
    }, (res) => {
      if (res?.status === 'ACTION_COMPLETED') sendResponse('ACTION_COMPLETED');
      else sendResponse('ACTION_FAILED', { reason: res?.reason || 'UNKNOWN' });
    });
  }
  else if (command === 'USER_INPUT_PROVIDED') {
    currentState = { status: 'RUNNING', process_id: currentProcessId };
    broadcastState();
    // In a real system, the process manager handles continuing the flow
  }
  else if (command === 'CONFIRM_SUBMISSION') {
    currentState = { status: 'RUNNING', process_id: currentProcessId };
    broadcastState();
  }
  else if (command === 'AUTH_COMPLETED_BY_USER') {
    currentState = { status: 'RUNNING', process_id: currentProcessId };
    broadcastState();
  }
}

function broadcastState() {
  chrome.runtime.sendMessage({ type: 'STATE_UPDATE', payload: currentState }).catch(() => {});
}

// Sidepanel requests state
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'GET_STATE') {
    sendResponse(currentState);
  }
});
