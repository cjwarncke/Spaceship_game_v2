import asyncio
import websockets
import json
import time

connected = set()

async def handler(websocket):
    # Register client
    connected.add(websocket)
    print(f"New client connected: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            data = json.loads(message)
            
            # Expect message to be like:
            # { "type": "chat_message", "player_id": 1, "message": "Hello" }
            if data.get("type") == "chat_message":
                broadcast_msg = json.dumps({
                    "type": "chat_message",
                    "player_id": data.get("player_id"),
                    "message": data.get("message"),
                    "timestamp": int(time.time())
                })
                
                # Broadcast to all connected clients
                await asyncio.gather(*[client.send(broadcast_msg) for client in connected])
                
    except websockets.exceptions.ConnectionClosedOK:
        print(f"Client disconnected normally: {websocket.remote_address}")
    except Exception as e:
        print(f"Connection handler failed: {e}")
    finally:
        connected.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

async def main():
    async with websockets.serve(handler, "localhost", 8768):
        print("Chat server running")
        await asyncio.Future()  # run forever

        

if __name__ == "__main__":
    asyncio.run(main())
