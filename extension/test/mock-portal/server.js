import http from 'http';

const mockHtml = `
<!DOCTYPE html>
<html>
<head>
  <title>Jaipur MC Grievance Portal</title>
</head>
<body>
  <h1>Civic Portal Homepage</h1>
  <button id="btnGrievance" onclick="location.href='/complaints/new'">Register Grievance</button>
</body>
</html>
`;

const formHtml = `
<!DOCTYPE html>
<html>
<head>
  <title>New Grievance</title>
</head>
<body>
  <h1>New Grievance</h1>
  <div id="formContainer">
    <input type="text" id="txtName" placeholder="Full Name" />
    <input type="text" id="txtMobile" placeholder="Mobile Number" />
    <select name="department">
      <option value="">Select Dept</option>
      <option value="1">Electricity / Streetlights</option>
      <option value="2">Water Supply</option>
    </select>
    <textarea id="txtAddress" placeholder="Ward Address"></textarea>
    
    <div id="otpSection" style="margin-top: 20px;">
      <button id="btnSendOtp">Send OTP</button>
      <input type="text" id="txtOtp" placeholder="OTP" style="display:none;" />
      <button id="btnVerifyOtp" style="display:none;">Verify OTP</button>
    </div>

    <button id="btnSubmitGrievance" style="margin-top: 20px;">Submit</button>
  </div>
  
  <div id="submissionSuccess" style="display:none;">
    <h2>Grievance submitted successfully.</h2>
  </div>

  <script>
    document.getElementById('btnSendOtp').onclick = () => {
      document.getElementById('txtOtp').style.display = 'block';
      document.getElementById('btnVerifyOtp').style.display = 'block';
    };
    
    document.getElementById('btnVerifyOtp').onclick = () => {
      alert('OTP Verified');
    };
    
    document.getElementById('btnSubmitGrievance').onclick = () => {
      document.getElementById('formContainer').style.display = 'none';
      document.getElementById('submissionSuccess').style.display = 'block';
    };
  </script>
</body>
</html>
`;

const server = http.createServer((req, res) => {
  if (req.url === '/complaints/new') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(formHtml);
  } else {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(mockHtml);
  }
});

server.listen(9000, () => {
  console.log('Mock Portal listening on http://localhost:9000');
});
