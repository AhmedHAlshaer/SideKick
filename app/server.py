"""
FastAPI server for Sidekick - Professional web interface
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sidekick import Sidekick
import json
import asyncio
from pathlib import Path

app = FastAPI(title="Sidekick")

# Store active sidekick instances per connection
active_sidekicks = {}

@app.get("/")
async def get():
    """Serve the main HTML page"""
    html_file = Path(__file__).parent / "static" / "index.html"
    with open(html_file, "r") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming"""
    await websocket.accept()
    
    # Create new Sidekick instance for this connection
    sidekick = Sidekick()
    await sidekick.setup()
    
    connection_id = id(websocket)
    active_sidekicks[connection_id] = sidekick
    
    try:
        # Send ready signal
        await websocket.send_json({
            "type": "ready",
            "message": "Connected to Sidekick"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "message":
                user_message = message_data["message"]
                success_criteria = message_data.get("success_criteria", "")
                
                # Send user message back
                await websocket.send_json({
                    "type": "user_message",
                    "content": user_message
                })
                
                # Stream assistant response
                history = []
                async for updated_history in sidekick.run_superstep_streaming(
                    user_message, success_criteria, history
                ):
                    if updated_history:
                        # Get last assistant message
                        for msg in reversed(updated_history):
                            if msg.get("role") == "assistant":
                                await websocket.send_json({
                                    "type": "assistant_message",
                                    "content": msg.get("content", "")
                                })
                                break
                
                # Send completion signal
                await websocket.send_json({
                    "type": "complete"
                })
            
            elif message_data["type"] == "stop":
                # Client requested to stop current generation
                await websocket.send_json({
                    "type": "stopped",
                    "message": "Generation stopped by user"
                })
                continue
            
            elif message_data["type"] == "reset":
                # Clean up old instance
                if connection_id in active_sidekicks:
                    active_sidekicks[connection_id].cleanup()
                
                # Create new instance
                sidekick = Sidekick()
                await sidekick.setup()
                active_sidekicks[connection_id] = sidekick
                
                await websocket.send_json({
                    "type": "reset_complete"
                })
    
    except WebSocketDisconnect:
        # Clean up on disconnect
        if connection_id in active_sidekicks:
            active_sidekicks[connection_id].cleanup()
            del active_sidekicks[connection_id]
    except Exception as e:
        print(f"Error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    import signal
    import sys
    
    def signal_handler(sig, frame):
        print("\n\n" + "="*60)
        print("🛑 Shutting down Sidekick...")
        print("="*60)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n" + "="*60)
    print("🚀 Sidekick Server Starting...")
    print("="*60)
    print("\n📍 Click this link: \033]8;;http://localhost:8000\033\\http://localhost:8000\033]8;;\033\\")
    print("   Or copy/paste: http://localhost:8000")
    print("\n💡 Press CTRL+C to stop\n")
    print("="*60 + "\n")
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("🛑 Sidekick stopped")
        print("="*60)

