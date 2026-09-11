import WebSocket from 'ws';


async function runMockExtension() {
  const processId = process.argv[2];
  if (!processId) {
    console.error("Please provide process_id as an argument");
    process.exit(1);
  }

  // 1. Register Extension
  const extensionId = "mock_ext_123";
  const res = await fetch('http://localhost:8000/v1/extensions/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      extension_id: extensionId,
      browser_session_id: "session_1",
      status: "ONLINE"
    })
  });
  console.log("Registered:", await res.json());

  // 2. Connect WebSocket
  const wsUrl = `ws://localhost:8000/v1/ws/${processId}`;
  console.log("Connecting to:", wsUrl);
  const ws = new WebSocket(wsUrl, { headers: { Origin: 'http://localhost' } });

  ws.on('open', () => {
    console.log('Mock Extension WebSocket Connected!');
  });

  ws.on('message', async (data) => {
    const message = JSON.parse(data.toString());
    console.log('\n--- Received Command ---');
    console.log(JSON.stringify(message, null, 2));

    const { command_id, command } = message;

    const sendResponse = (event, payload = {}) => {
      console.log(`Sending Response: ${event}`);
      ws.send(JSON.stringify({ event, command_id, payload }));
    };

    if (command === 'OPEN_TAB') {
      setTimeout(() => sendResponse('TAB_CREATED', { tab_id: 1, url: message.payload.url }), 500);
    } else if (['NAVIGATE', 'CLICK_SELECTOR', 'FILL_FIELD', 'SELECT_OPTION'].includes(command)) {
      setTimeout(() => sendResponse('ACTION_COMPLETED'), 500);
    } else if (command === 'USER_INPUT_PROVIDED') {
      console.log("Input provided by user!");
    } else if (command === 'AUTH_COMPLETED_BY_USER') {
      console.log("Auth completed by user!");
    } else if (command === 'CONFIRM_SUBMISSION') {
      console.log("Submission confirmed by user!");
    } else {
      console.log("Unknown command:", command);
    }
  });

  ws.on('close', () => {
    console.log("WebSocket closed");
  });
}

runMockExtension();
