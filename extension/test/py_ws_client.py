import asyncio
import websockets
import sys
import json

async def test(pid):
    uri = f"ws://localhost:8000/v1/ws/{pid}"
    try:
        async with websockets.connect(uri) as ws:
            print("Connected!")
            while True:
                msg = await ws.recv()
                print(msg)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test(sys.argv[1]))
