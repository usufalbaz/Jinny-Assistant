"""
Jinny Core - Production FastAPI Server & Gateway Entry Point
Architected & Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)

Features:
- Secured Gateway with X-Jinny-Api-Key verification
- Endpoints for Agent Intent reasoning, Semantic Memory Search, and IoT control
- Bi-directional WebSocket Telephony Bridge with authentication & telemetry reporting
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Security, status, Query
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings
from core.memory import PersistentMemoryStore
from core.sms_dispatcher import SmsDispatcher
from core.iot_controller import IoTController
from core.assistant import JinnyAssistantCore

# إعداد الـ Logging الاحترافي المنظم
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s : %(message)s"
)
logger = logging.getLogger("Jinny.Server")

# إنشاء الكائنات المشتركة (Singletons)
memory_store = PersistentMemoryStore()
sms_dispatcher = SmsDispatcher()
iot_controller = IoTController()
assistant_core = JinnyAssistantCore(memory_store, sms_dispatcher, iot_controller)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Jinny Core Enterprise Subsystems...")
    await memory_store.initialize()
    logger.info(f"Jinny Core online and listening on {settings.HOST}:{settings.PORT}")
    yield
    logger.info("Gracefully shutting down Jinny Core services.")


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

# ----------------- طبقة الأمان (Security & Authentication) -----------------
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    """التحقق من صحة مفتاح الـ API الممرر في الهيدر"""
    if settings.DEBUG:
        return True  # السماح بالتجاوز في وضع التطوير والتجارب فقط
    if not api_key or api_key != settings.JINNY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Jinny API Key"
        )
    return True


# ----------------- نماذج البيانات (Pydantic Schemas) -----------------
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


# ----------------- مسارات الـ API (REST Endpoints) -----------------
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
    """إرسال أمر صوتي/نصي للـ Agent ومعالجته بالذكاء الاصطناعي واستدعاء الأدوات"""
    try:
        response = await assistant_core.process_user_intent(req.query, req.metadata)
        return response
    except Exception as e:
        logger.error(f"Inference gateway error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/memory/search", dependencies=[Depends(verify_api_key)])
async def search_memory(req: SemanticSearchRequest):
    """البحث الدلالي الذكي في الذاكرة عبر الـ Vector Embeddings"""
    results = await memory_store.semantic_search(
        query=req.query,
        limit=req.limit,
        score_threshold=req.score_threshold
    )
    return {"query": req.query, "matches_count": len(results), "results": results}


@app.post("/api/sms/dispatch", dependencies=[Depends(verify_api_key)])
async def dispatch_sms(req: SmsDispatchRequest):
    """إرسال أمر SMS للشريحة عبر الأندرويد"""
    return await sms_dispatcher.dispatch_silent_sms(req.recipient, req.message, req.priority)


@app.get("/api/sms/tasks", dependencies=[Depends(verify_api_key)])
async def get_sms_task_queue():
    """عرض سجل الرسائل والرسائل المعلقة في الانتظار"""
    return {
        "pending_queue_count": len(sms_dispatcher.pending_queue),
        "history_count": len(sms_dispatcher.history_records),
        "history": list(sms_dispatcher.history_records.values())
    }


@app.get("/api/iot/devices", dependencies=[Depends(verify_api_key)])
async def list_iot_devices():
    """عرض أجهزة المنزل الذكي المسجلة"""
    return iot_controller.list_devices()


@app.post("/api/iot/execute", dependencies=[Depends(verify_api_key)])
async def execute_iot_command(req: IoTCommandRequest, _=Depends(verify_api_key)):
    """تنفيذ أمر IoT مباشر على جهاز محدد"""
    return await iot_controller.execute_device_command(req.device_id, req.action, req.params)


# ----------------- جسر الأندرويد (WebSocket Telephony Bridge) -----------------
@app.websocket("/ws/android-bridge")
async def android_telemetry_bridge(
    websocket: WebSocket,
    client_id: str = Query("android_primary"),
    token: Optional[str] = Query(None)
):
    """
    جسر الاتصال الحي والمستمر مع تطبيق الخلفية في هاتف الأندرويد
    """
    # التحقق من مفتاح الـ API للـ WebSocket
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
