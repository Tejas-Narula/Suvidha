import { WebSocketServer } from 'ws';
import http from 'http';

// 1. Setup Mock Website
const mockHtml = `
<!DOCTYPE html>
<html>
<body>
  <h1>Mock Test Portal</h1>
  <button id="startForm">Open Form</button>
  <div id="formContainer" style="display:none; margin-top: 20px;">
    <input type="text" id="txtName" placeholder="Full Name" />
    <br><br>
    <button id="btnSubmit">Submit</button>
  </div>
  <script>
    document.getElementById('startForm').onclick = () => {
      document.getElementById('formContainer').style.display = 'block';
    };
    document.getElementById('btnSubmit').onclick = () => {
      alert('Submitted: ' + document.getElementById('txtName').value);
    };
  </script>
</body>
</html>
`;

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(mockHtml);
});
server.listen(9000, () => console.log('Mock website running on http://localhost:9000'));

// 2. Setup WebSocket Server to act as the Backend
const wss = new WebSocketServer({ port: 8000 });
console.log('WebSocket server running on ws://localhost:8000');

wss.on('connection', (ws) => {
  console.log('Extension connected!');

  const plan = [
    { command_id: 'cmd_1', command: 'OPEN_TAB', payload: { url: 'http://localhost:9000' }, waitEvent: 'TAB_CREATED' },
    { command_id: 'cmd_2', command: 'CLICK_SELECTOR', payload: { selector: '#startForm' }, waitEvent: 'ACTION_COMPLETED', waitMs: 1000 },
    { command_id: 'cmd_3', command: 'FILL_FIELD', payload: { selector: '#txtName', value: 'Aryan Sharma' }, waitEvent: 'ACTION_COMPLETED' },
    { command_id: 'cmd_4', command: 'REQUEST_CONFIRMATION', payload: { message: 'Form is ready. Submit?' }, waitEvent: 'CONFIRMATION_RESPONSE' },
    { command_id: 'cmd_5', command: 'CLICK_SELECTOR', payload: { selector: '#btnSubmit' }, waitEvent: 'ACTION_COMPLETED' }
  ];

  let step = 0;

  function executeNext() {
    if (step >= plan.length) {
      console.log('✅ All steps completed successfully!');
      return;
    }
    const current = plan[step];
    console.log(`Sending command: ${current.command}`);
    
    if (current.waitMs) {
      setTimeout(() => {
        ws.send(JSON.stringify(current));
      }, current.waitMs);
    } else {
      ws.send(JSON.stringify(current));
    }
  }

  ws.on('message', (message) => {
    const response = JSON.parse(message.toString());
    console.log('Received:', response);
    
    const current = plan[step];
    if (response.event === current.waitEvent && response.command_id === current.command_id) {
      step++;
      setTimeout(executeNext, 500); // slight delay between steps for visibility
    }
  });

  // Start execution after 2 seconds
  setTimeout(executeNext, 2000);
});
