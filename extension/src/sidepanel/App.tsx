import React, { useEffect, useState } from 'react';

export default function App() {
  const [state, setState] = useState<any>({ status: 'DISCONNECTED', session_id: '' });
  const [sessionIdInput, setSessionIdInput] = useState('');

  useEffect(() => {
    const handleMessage = (message: any) => {
      if (message.type === 'STATE_UPDATE') {
        setState(message.payload);
      }
    };
    chrome.runtime.onMessage.addListener(handleMessage);
    
    chrome.runtime.sendMessage({ type: 'GET_STATE' }, (response) => {
      if (response) setState(response);
    });

    return () => chrome.runtime.onMessage.removeListener(handleMessage);
  }, []);

  const connectSession = (e: React.FormEvent) => {
    e.preventDefault();
    if (sessionIdInput) {
      chrome.runtime.sendMessage({ type: 'CONNECT_SESSION', session_id: sessionIdInput });
    }
  };

  return (
    <div style={{ padding: '16px' }}>
      <h2>Suvidha Agent</h2>
      
      {state.status === 'DISCONNECTED' ? (
        <form onSubmit={connectSession} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label>Enter Session ID (from Voice Agent):</label>
          <input 
            type="text" 
            value={sessionIdInput}
            onChange={(e) => setSessionIdInput(e.target.value)}
            placeholder="sess_..."
            required 
            style={{ padding: '8px', borderRadius: '4px', border: '1px solid #d1d5db' }} 
          />
          <button type="submit" style={{ background: '#4f46e5', color: 'white', border: 'none', padding: '8px', borderRadius: '4px', cursor: 'pointer' }}>
            Connect
          </button>
        </form>
      ) : (
        <div style={{ padding: '12px', background: '#fff', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <strong>Status:</strong> {state.status}
          <br/>
          <strong>Session ID:</strong> {state.session_id}
          <br/>
          <strong>Service:</strong> {state.service_title || 'Pending...'}
        </div>
      )}

      {state.status === 'OTP_REQUIRED' && (
        <div style={{ padding: '12px', background: '#fee2e2', borderRadius: '8px', border: '1px solid #fecaca', marginTop: '16px' }}>
          <h3>OTP Required</h3>
          <p>Please wait for the user to provide the OTP via the Voice Agent.</p>
        </div>
      )}

      {state.status === 'FIELD_REQUIRED' && (
        <div style={{ padding: '12px', background: '#fffbeb', borderRadius: '8px', border: '1px solid #fde68a', marginTop: '16px' }}>
          <h3>Missing Information</h3>
          <p>Waiting for user to provide: {state.missing_field}</p>
        </div>
      )}
      
      {state.status === 'READY_FOR_SUBMISSION' && (
        <div style={{ padding: '12px', background: '#eef2ff', borderRadius: '8px', border: '1px solid #c7d2fe', marginTop: '16px' }}>
          <h3>Form Ready</h3>
          <p>Form is filled. Waiting for user confirmation via Voice Agent.</p>
        </div>
      )}
    </div>
  );
}
