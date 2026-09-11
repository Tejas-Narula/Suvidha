import React, { useEffect, useState } from 'react';

export default function App() {
  const [state, setState] = useState<any>({ status: 'WAITING_FOR_PROCESS' });

  useEffect(() => {
    const handleMessage = (message: any) => {
      if (message.type === 'STATE_UPDATE') {
        setState(message.payload);
      }
    };
    chrome.runtime.onMessage.addListener(handleMessage);
    
    // Request initial state
    chrome.runtime.sendMessage({ type: 'GET_STATE' }, (response) => {
      if (response) setState(response);
    });

    return () => chrome.runtime.onMessage.removeListener(handleMessage);
  }, []);

  const handleConfirm = async () => {
    await fetch(`http://localhost:8000/v1/automations/${state.process_id}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirmed: true })
    });
    setState({ ...state, status: 'RUNNING' });
  };

  const handleCancel = async () => {
    await fetch(`http://localhost:8000/v1/automations/${state.process_id}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirmed: false })
    });
    setState({ ...state, status: 'RUNNING' });
  };

  const handleAuthComplete = async () => {
    await fetch(`http://localhost:8000/v1/automations/${state.process_id}/auth-complete`, {
      method: 'POST'
    });
    setState({ ...state, status: 'RUNNING' });
  };

  const submitUserInput = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const value = formData.get('inputValue');
    await fetch(`http://localhost:8000/v1/automations/${state.process_id}/input`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ field_name: state.question_field, value })
    });
    setState({ ...state, status: 'RUNNING' });
  };

  return (
    <div style={{ padding: '16px' }}>
      <h2>Suvidha Agent</h2>
      <div style={{
        padding: '12px',
        background: '#fff',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '16px'
      }}>
        <strong>Status:</strong> {state.status}
        <br/>
        <strong>Process ID:</strong> {state.process_id || 'N/A'}
      </div>

      {state.status === 'WAITING_FOR_CONFIRMATION' && (
        <div style={{
          padding: '12px',
          background: '#eef2ff',
          borderRadius: '8px',
          border: '1px solid #c7d2fe'
        }}>
          <h3>Form Ready</h3>
          <p>The form is ready for submission.</p>
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <button onClick={handleConfirm} style={{
              background: '#4f46e5', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer'
            }}>Confirm Submission</button>
            <button onClick={handleCancel} style={{
              background: '#fff', border: '1px solid #d1d5db', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer'
            }}>Cancel</button>
          </div>
        </div>
      )}

      {state.status === 'WAITING_FOR_AUTH' && (
        <div style={{
          padding: '12px',
          background: '#fee2e2',
          borderRadius: '8px',
          border: '1px solid #fecaca'
        }}>
          <h3>Authentication Required</h3>
          <p>Complete authentication (e.g. OTP) in the browser.</p>
          <button onClick={handleAuthComplete} style={{
            background: '#ef4444', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', marginTop: '8px'
          }}>I have completed it</button>
        </div>
      )}

      {state.status === 'WAITING_FOR_USER' && (
        <div style={{
          padding: '12px',
          background: '#fffbeb',
          borderRadius: '8px',
          border: '1px solid #fde68a'
        }}>
          <h3>Input Required</h3>
          <p>{state.question}</p>
          <form onSubmit={submitUserInput} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <input type="text" name="inputValue" required style={{
              padding: '8px', borderRadius: '4px', border: '1px solid #d1d5db'
            }} />
            <button type="submit" style={{
              background: '#d97706', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer'
            }}>Submit</button>
          </form>
        </div>
      )}
    </div>
  );
}
