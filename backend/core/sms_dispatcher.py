"""
Jinny Core - Silent SMS Dispatch & Telephony Bridge
Engineered by Eng. Yousuf Albaz
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

logger = logging.getLogger("Jinny.SMS")

class SmsTask(BaseModel):
    id: str
    recipient: str
    message: str
    priority: int = 1 # 1: normal, 2: urgent, 3: emergency
    scheduled_at: Optional[datetime] = None
    status: str = "pending" # pending, queued_for_device, dispatched, delivered, failed

class SmsDispatcher:
    def __init__(self):
        self.pending_queue: List[SmsTask] = []
        self.active_android_clients: Dict[str, Any] = {} # websocket client connections

    def register_android_client(self, client_id: str, ws: Any):
        self.active_android_clients[client_id] = ws
        logger.info(f"Android telemetry node registered: {client_id}")

    def unregister_android_client(self, client_id: str):
        if client_id in self.active_android_clients:
            del self.active_android_clients[client_id]
            logger.info(f"Android telemetry node disconnected: {client_id}")

    async def dispatch_silent_sms(self, recipient: str, message: str, priority: int = 1) -> Dict[str, Any]:
        task_id = f"sms_{int(datetime.utcnow().timestamp())}_{abs(hash(recipient)) % 10000}"
        task = SmsTask(
            id=task_id,
            recipient=recipient,
            message=message,
            priority=priority,
            status="pending"
        )

        logger.info(f"Initiating silent SMS dispatch -> {recipient} (Task ID: {task_id})")

        # Check if an Android client is connected via WebSocket
        if self.active_android_clients:
            # Deliver command to the primary Android client
            client_id, ws = next(iter(self.active_android_clients.items()))
            payload = {
                "command": "DISPATCH_SMS",
                "task_id": task.id,
                "phone_number": task.recipient,
                "message": task.message,
                "silent": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                await ws.send_json(payload)
                task.status = "queued_for_device"
                return {
                    "status": "success",
                    "task_id": task.id,
                    "target_client": client_id,
                    "message": "Dispatched to background Android Telephony Service"
                }
            except Exception as e:
                logger.error(f"Failed to transmit SMS task to Android device: {e}")
                task.status = "failed"
                return {"status": "error", "error": str(e)}
        else:
            self.pending_queue.append(task)
            return {
                "status": "queued",
                "task_id": task.id,
                "message": "No active Android bridge online. Task queued for auto-dispatch upon connection."
            }

    async def flush_queued_tasks_for_client(self, ws: Any):
        while self.pending_queue:
            task = self.pending_queue.pop(0)
            payload = {
                "command": "DISPATCH_SMS",
                "task_id": task.id,
                "phone_number": task.recipient,
                "message": task.message,
                "silent": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            await ws.send_json(payload)
            logger.info(f"Flushed queued SMS task {task.id} to Android node")
