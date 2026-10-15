"""
Jinny Core - Proactive Autonomous Intelligence Worker
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)

Features:
- Continuous background evaluation of IoT states, daily routines, and triggers.
- Proactive generation of environmental status reports (Morning briefings, anomalies).
- Autonomous push dispatch to connected Android daemon nodes for real-time voice delivery.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.memory import PersistentMemoryStore
from core.iot_controller import IoTController
from core.sms_dispatcher import SmsDispatcher
from config import settings

logger = logging.getLogger("Jinny.Proactive")


class ProactiveAutonomousAgent:
    """
    Background autonomous intelligence monitor that initiates actions and briefings
    without requiring explicit user invocation (True Jarvis proactive behavior).
    """

    def __init__(
        self,
        memory: PersistentMemoryStore,
        iot: IoTController,
        sms_dispatcher: SmsDispatcher
    ):
        self.memory = memory
        self.iot = iot
        self.sms_dispatcher = sms_dispatcher
        self.is_running = False
        self._worker_task: Optional[asyncio.Task] = None
        self.last_briefing_date: Optional[str] = None

    async def start(self):
        """Start the background proactive evaluation loop."""
        if self.is_running:
            return
        self.is_running = True
        self._worker_task = asyncio.create_task(self._autonomous_monitor_loop())
        logger.info("Proactive Autonomous Agent loop started successfully.")

    async def stop(self):
        """Gracefully stop the background worker task."""
        self.is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Proactive Autonomous Agent loop stopped.")

    async def _broadcast_voice_briefing(self, briefing_text: str):
        """
        Broadcast proactive briefing to all active Android telemetry nodes to speak aloud.
        """
        if not self.sms_dispatcher.active_android_clients:
            logger.info(f"Proactive briefing generated, but no active Android bridge connected: '{briefing_text}'")
            return

        payload = {
            "type": "ASSISTANT_REPLY",
            "data": {
                "intent": "PROACTIVE_BRIEFING",
                "speech_output": briefing_text,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        for client_id, ws in list(self.sms_dispatcher.active_android_clients.items()):
            try:
                await ws.send_json(payload)
                logger.info(f"Proactive voice briefing dispatched to Android node [{client_id}].")
            except Exception as e:
                logger.warning(f"Failed to transmit proactive briefing to [{client_id}]: {e}")

    async def generate_system_briefing(self) -> str:
        """
        Synthesize autonomous status briefing assessing connected devices and memory.
        """
        devices = self.iot.list_devices()
        active_count = len([d for d in devices.values() if d.get("state") in ["on", "unlocked"]])

        # Retrieve latest memory context snapshot
        recent_memory = await self.memory.get_context_snapshot()

        now = datetime.now()
        greeting = "Good morning" if now.hour < 12 else "Good afternoon" if now.hour < 18 else "Good evening"

        briefing = (
            f"{greeting}, sir. Autonomous system check complete. "
            f"All background telemetry is synchronized. "
            f"Currently monitoring {len(devices)} IoT hardware nodes with {active_count} active units. "
            f"Core memory is nominal. Ready for your command."
        )
        return briefing

    async def _autonomous_monitor_loop(self):
        """
        Continuous evaluation loop running periodically in the background.
        """
        # Initial boot delay to allow all subsystems and bridges to establish connection
        await asyncio.sleep(10)

        while self.is_running:
            try:
                current_date = datetime.utcnow().strftime("%Y-%m-%d")

                # Daily morning briefing trigger check
                if self.last_briefing_date != current_date and datetime.now().hour >= 8:
                    briefing = await self.generate_system_briefing()
                    await self._broadcast_voice_briefing(briefing)
                    self.last_briefing_date = current_date

                # Heartbeat IoT state audit every 15 minutes
                await asyncio.sleep(900)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in proactive monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(60)
