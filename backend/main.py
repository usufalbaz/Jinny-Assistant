"""
Jinny Core - Production FastAPI Server Entry Point
Architected & Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

from config import settings
from core.memory import PersistentMemoryStore
from core.sms_dispatcher import SmsDispatcher
from core.iot_controller import IoTController
from core.assistant import JinnyAssistantCore

# Structured Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s : %(message)s"
)
logger = logging.getLogger("Jinny.Server")

# Instantiate Core Singletons
memory_store = PersistentMemoryStore()
sms_dispatcher = SmsDispatcher()
iot_controller = IoTController()
assistant_core = JinnyAssistantCore(memory_store, sms_dispatcher, iot_controller)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Jinny Core Assistant Subsystems...")
    await memory_store.initialize()
    logger.info(f"Jinny Core online and listening on {settings.HOST}:{settings.PORT}")
    yield
    logger.info("Gracefully shutting down Jinny Core services.")

app = FastAPI(
    title="Jinny Core AI Assistant Backend",
    version=settings.VERSION,
    description="Jarvis-inspired Autonomous System & IoT Orchestrator for Android and Edge Devices",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Schemas
class QueryRequest(BaseModel):
    query: str
    client_id: Optional[str] = "android_node_1"
    metadata: Optional[Dict[str, Any]] = None

class SmsDispatchRequest(BaseModel):
    recipient: str
    message: str
    priority: Optional[int] = 1

class IoTCommandRequest(BaseModel):
    device_id: str
    action: str
    params: Optional[Dict[str, Any]] = None

# Routes
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "system": "Jinny Core",
        "version": settings.VERSION,
        "author": "Eng. Yousuf Albaz (AI & Systems Engineer)"
    }

@app.post("/api/assistant/interact")
async def interact_with_assistant(req: QueryRequest):
    try:
        response = await assistant_core.process_user_intent(req.query, req.metadata)
        return response
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sms/dispatch")
async def dispatch_sms(req: SmsDispatchRequest):
    result = await sms_dispatcher.dispatch_silent_sms(req.recipient, req.message, req.priority)
    return result

@app.get("/api/iot/devices")
async def list_iot_devices():
    return iot_controller.list_devices()

@app.post("/api/iot/execute")
async def execute_iot_command(req: IoTCommandRequest):
    return await iot_controller.execute_device_command(req.device_id, req.action, req.params)

# Android Background Bridge WebSocket
@app.websocket("/ws/android-bridge")
async def android_telemetry_bridge(websocket: WebSocket, client_id: str = "android_primary"):
    await websocket.accept()
    sms_dispatcher.register_android_client(client_id, websocket)
    await sms_dispatcher.flush_queued_tasks_for_client(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("type")
            
            if command == "HEARTBEAT":
                await websocket.send_json({"type": "PONG", "timestamp": data.get("timestamp")})
            elif command == "VOICE_STREAM_INPUT":
                text = data.get("text", "")
                res = await assistant_core.process_user_intent(text)
                await websocket.send_json({"type": "ASSISTANT_REPLY", "data": res})
            elif command == "SMS_DELIVERY_REPORT":
                task_id = data.get("task_id")
                status = data.get("status")
                logger.info(f"SMS Delivery confirmation received from Android: {task_id} -> {status}")
    except WebSocketDisconnect:
        sms_dispatcher.unregister_android_client(client_id)
    except Exception as e:
        logger.error(f"WebSocket error on Android bridge: {e}")
        sms_dispatcher.unregister_android_client(client_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
