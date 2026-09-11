import asyncio
import websockets
import json
import httpx
import time

async def test_correction():
    # 1. Start a session
    print("Starting session...")
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://suvidha-g37k.onrender.com/api/submit/voice", json={
            "session_id": "test_sess_" + str(int(time.time())),
            "user_query": "I want to file a train complaint on railmadad",
            "service_type": "Rail Madad Grievance"
        })
        session = resp.json()
        session_id = session["session_id"]
        print(f"Session created: {session_id}")

    # 2. Connect WebSocket
    print("Connecting WebSocket...")
    async with websockets.connect(f"wss://suvidha-g37k.onrender.com/ws/browser/{session_id}") as ws:
        print("Connected!")
        
        # 3. Simulate correction
        print("Sending correction API call...")
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://suvidha-g37k.onrender.com/api/submit", json={
                "submission_id": "SUB_" + session_id,
                "provided_field": "Mobile No.",
                "provided_value": "9876543210"
            })
            print("Correction response:", resp.status_code)
        
        # 4. Wait for WebSocket message
        print("Waiting for WS message...")
        while True:
            msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(msg)
            print("Received WS command:", data["command"])
            
            # Print field value
            for f in data["form_filling"]["fields"]:
                if "mobile" in f["field_name"].lower():
                    print("Mobile Field Value in Payload:", f["value"])
            break

asyncio.run(test_correction())
