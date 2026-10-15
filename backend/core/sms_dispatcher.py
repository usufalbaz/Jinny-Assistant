"""
Jinny Core - Resilient SMS Dispatch & Telephony Subsystem
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)

Features:
- Cellular SMS task dispatching through host Android background daemon
- Phone number normalization & input sanitization
- Delivery acknowledgment and retry-count lifecycle tracking
- Offline queue buffering with automatic sync upon Android reconnection
"""

import logging
import asyncio
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger("Jinny.SMS")


class SmsTask(BaseModel):
    id: str
    recipient: str
    message: str
    priority: int = 1  # 1: Normal, 2: Urgent, 3: Emergency
    status: str = "pending"  # pending, queued_for_device, dispatched, delivered, failed
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    delivered_at: Optional[str] = None
    error_reason: Optional[str] = None


class SmsDispatcher:
    def __init__(self):
        self.pending_queue: List[SmsTask] = []
        self.history_records: Dict[str, SmsTask] = {}
        self.active_android_clients: Dict[str, Any] = {}

    @staticmethod
    def _sanitize_phone_number(raw_number: str) -> str:
        """
        تنظيف وفلترة رقم الهاتف وإزالة المسافات والشرطات غير الصالحة
        """
        # السماح بعلامة + لكود الدولة والأرقام فقط
        cleaned = re.sub(r"[^\d+]", "", raw_number.strip())
        return cleaned

    def register_android_client(self, client_id: str, ws: Any):
        """تسجيل اتصال هاتف أندرويد جديد عبر الـ WebSocket"""
        self.active_android_clients[client_id] = ws
        logger.info(f"Android Telephony Node registered: [{client_id}] (Total active: {len(self.active_android_clients)})")

    def unregister_android_client(self, client_id: str):
        """إلغاء تسجيل الهاتف عند انقطاع الاتصال"""
        if client_id in self.active_android_clients:
            del self.active_android_clients[client_id]
            logger.info(f"Android Telephony Node disconnected: [{client_id}]")

    async def dispatch_silent_sms(self, recipient: str, message: str, priority: int = 1) -> Dict[str, Any]:
        """
        بدء عملية إرسال الـ SMS وتوجيهها لجهاز الأندرويد المتصل أو وضعها في الانتظار
        """
        clean_recipient = self._sanitize_phone_number(recipient)
        if not clean_recipient or len(clean_recipient) < 3:
            return {"status": "error", "message": f"Invalid phone number provided: '{recipient}'"}

        task_id = f"sms_{int(datetime.utcnow().timestamp())}_{abs(hash(clean_recipient)) % 10000}"
        task = SmsTask(
            id=task_id,
            recipient=clean_recipient,
            message=message.strip(),
            priority=priority,
            status="pending"
        )

        self.history_records[task_id] = task
        logger.info(f"Created SMS Task {task_id} -> {clean_recipient} (Priority: {priority})")

        # لو فيه جهاز أندرويد متصل حالياً بالسيرفر، نرسل الأمر فوراً
        if self.active_android_clients:
            client_id, ws = next(iter(self.active_android_clients.items()))
            payload = {
                "command": "DISPATCH_SMS",
                "task_id": task.id,
                "phone_number": task.recipient,
                "message": task.message,
                "silent": True,
                "priority": task.priority,
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                await ws.send_json(payload)
                task.status = "queued_for_device"
                return {
                    "status": "success",
                    "task_id": task.id,
                    "target_device": client_id,
                    "message": "Dispatched to background Android Telephony daemon"
                }
            except Exception as e:
                logger.error(f"Failed to transmit SMS task to Android WebSocket: {e}")
                task.status = "pending"
                task.retry_count += 1
                self.pending_queue.append(task)
                return {"status": "queued", "task_id": task.id, "warning": "Connection interrupted, re-queued."}
        else:
            # لو الموبايل Offline بنحطها في قائمة الانتظار لحد ما يتصل
            self.pending_queue.append(task)
            return {
                "status": "queued",
                "task_id": task.id,
                "message": "No active Android bridge online. Task queued for automatic flush upon reconnect."
            }

    async def flush_queued_tasks_for_client(self, ws: Any):
        """
        تفريغ وإرسال كل الرسائل المعلقة بمجرد إعادة اتصال الهاتف بالسيرفر
        """
        if not self.pending_queue:
            return

        logger.info(f"Flushing {len(self.pending_queue)} queued SMS tasks to newly connected Android device...")
        # ترتيب الرسائل حسب الأولوية (Priority 3 -> 2 -> 1)
        self.pending_queue.sort(key=lambda t: t.priority, reverse=True)

        while self.pending_queue:
            task = self.pending_queue.pop(0)
            payload = {
                "command": "DISPATCH_SMS",
                "task_id": task.id,
                "phone_number": task.recipient,
                "message": task.message,
                "silent": True,
                "priority": task.priority,
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                await ws.send_json(payload)
                task.status = "queued_for_device"
                logger.info(f"Successfully flushed queued task: {task.id}")
                await asyncio.sleep(0.5)  # فاصل زمني لتفادي خنق الـ Modem في الأندرويد
            except Exception as e:
                logger.error(f"Error flushing task {task.id}: {e}")
                task.status = "failed"
                task.error_reason = str(e)
                break

    def record_delivery_report(self, task_id: str, status: str, error: Optional[str] = None):
        """
        تسجيل تقرير التسليم القادم من الأندرويد بعد محاولة إرسال الشريحة الفعلية
        """
        if task_id in self.history_records:
            task = self.history_records[task_id]
            task.status = status
            if status == "delivered" or status == "dispatched":
                task.delivered_at = datetime.utcnow().isoformat()
            if error:
                task.error_reason = error
            logger.info(f"Updated SMS Task status: {task_id} -> {status}")
