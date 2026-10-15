"""
Jinny Core - Production FastAPI Server & Gateway Entry Point
Architected & Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)

Features:
- Secured Gateway with X-Jinny-Api-Key verification
- Endpoints for Agent Intent reasoning, Semantic Memory Search, IoT control, and Neural Voice Synthesis
- Proactive Autonomous Intelligence worker integration in application lifespan
- Bi-directional WebSocket Telephony Bridge with authentication & telemetry reporting
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Security, status, Query
from fastapi.responses import Response
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings
from core.memory import PersistentMemoryStore
from core.sms_dispatcher import SmsDispatcher
from core.iot_controller import IoTController
from core.assistant import JinnyAssistantCore
from core.voice_engine import NeuralVoiceEngine
from core.proactive_agent import ProactiveAutonomousAgent

# Structured logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s : %(message)s"
)
logger = logging.getLogger("Jinny.Server")

# Instantiate core subsystem singletons
memory_store = PersistentMemoryStore()
sms_dispatcher = SmsDispatcher()
iot_controller = IoTController()
voice_engine = NeuralVoiceEngine()
assistant_core = JinnyAssistantCore(memory_store, sms_dispatcher, iot_controller)
proactive_agent = ProactiveAutonomousAgent(memory_store, iot_controller, sms_dispatcher)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Jinny Core Enterprise Subsystems...")
    await memory_store.initialize()
    # Start background proactive intelligence worker
    await proactive_agent.start()
    logger.info(f"Jinny Core online and listening on {settings.HOST}:{settings.PORT}")
    yield
    logger.info("Gracefully shutting down Jinny Core services...")
    await proactive_agent.stop()
    logger.info("Jinny Core services stopped.")


app = FastAPI(
    title="Jinny Core AI Assistant Gateway",
    version=settings.VERSION,
    description="Jarvis-inspired Autonomous System & IoT Telephony Orchestrator",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Security & Gateway Protection Layer -----------------
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    """Validate API key passed in request header."""
    if settings.DEBUG:
        return True  # Allow bypass in local development/debug mode only
    if not api_key or api_key != settings.JINNY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Jinny API Key"
        )
    return True


# ----------------- Pydantic Request & Response Schemas -----------------
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


class SemanticSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    score_threshold: Optional[float] = 0.4


class VoiceSynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None


# ----------------- REST API Endpoints -----------------
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "system": "Jinny Core",
        "version": settings.VERSION,
        "author": "Eng. Yousuf Albaz (AI & Systems Engineer)"
    }


@app.post("/api/assistant/interact", dependencies=[Depends(verify_api_key)])
async def interact_with_assistant(req: QueryRequest):
    """Process voice or text intent via autonomous agentic loop."""
    try:
        response = await assistant_core.process_user_intent(req.query, req.metadata)
        return response
    except Exception as e:
        logger.error(f"Inference gateway error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/synthesize", dependencies=[Depends(verify_api_key)])
async def synthesize_voice(req: VoiceSynthesizeRequest):
    """Synthesize text into streaming neural MP3 audio."""
    try:
        audio_bytes = await voice_engine.synthesize_speech(req.text, req.voice)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Voice synthesis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/search", dependencies=[Depends(verify_api_key)])
async def search_memory(req: SemanticSearchRequest):
    """Perform semantic similarity search on cognitive memory store."""
    results = await memory_store.semantic_search(
        query=req.query,
        limit=req.limit,
        score_threshold=req.score_threshold
    )
    return {"query": req.query, "matches_count": len(results), "results": results}


@app.post("/api/sms/dispatch", dependencies=[Depends(verify_api_key)])
async def dispatch_sms(req: SmsDispatchRequest):
    """Dispatch programmatic SMS task to connected Android daemon."""
    return await sms_dispatcher.dispatch_silent_sms(req.recipient, req.message, req.priority)


@app.get("/api/sms/tasks", dependencies=[Depends(verify_api_key)])
async def get_sms_task_queue():
    """Retrieve active SMS queue and delivery history records."""
    return {
        "pending_queue_count": len(sms_dispatcher.pending_queue),
        "history_count": len(sms_dispatcher.history_records),
        "history": list(sms_dispatcher.history_records.values())
    }


@app.get("/api/iot/devices", dependencies=[Depends(verify_api_key)])
async def list_iot_devices():
    """List all registered smart home and IoT devices."""
    return iot_controller.list_devices()


@app.post("/api/iot/execute", dependencies=[Depends(verify_api_key)])
async def execute_iot_command(req: IoTCommandRequest):
    """Execute hardware command on specific registered IoT device."""
    return await iot_controller.execute_device_command(req.device_id, req.action, req.params)


@app.post("/api/proactive/trigger", dependencies=[Depends(verify_api_key)])
async def trigger_proactive_briefing():
    """Manually trigger and broadcast an autonomous Jarvis status briefing."""
    briefing = await proactive_agent.generate_system_briefing()
    await proactive_agent._broadcast_voice_briefing(briefing)
    return {"status": "broadcasted", "briefing": briefing}


# ----------------- Android WebSocket Telephony Bridge -----------------
@app.websocket("/ws/android-bridge")
async def android_telemetry_bridge(
    websocket: WebSocket,
    client_id: str = Query("android_primary"),
    token: Optional[str] = Query(None)
):
    """Bidirectional WebSocket telemetry bridge for Android background daemon."""
    # Authenticate incoming WebSocket connection token
    if not settings.DEBUG and token != settings.JINNY_API_KEY:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.warning(f"Rejected unauthorized WebSocket connection attempt from: {client_id}")
        return

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
                delivery_status = data.get("status")
                error_msg = data.get("error")
                sms_dispatcher.record_delivery_report(task_id, delivery_status, error_msg)

    except WebSocketDisconnect:
        sms_dispatcher.unregister_android_client(client_id)
    except Exception as e:
        logger.error(f"WebSocket error on bridge [{client_id}]: {e}")
        sms_dispatcher.unregister_android_client(client_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
