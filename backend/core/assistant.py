"""
Jinny Core - Jarvis-Inspired Cognitive Assistant Orchestrator
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.memory import PersistentMemoryStore
from core.sms_dispatcher import SmsDispatcher
from core.iot_controller import IoTController
from config import settings

logger = logging.getLogger("Jinny.Orchestrator")

class JinnyAssistantCore:
    def __init__(
        self,
        memory: PersistentMemoryStore,
        sms_dispatcher: SmsDispatcher,
        iot_controller: IoTController
    ):
        self.memory = memory
        self.sms_dispatcher = sms_dispatcher
        self.iot = iot_controller
        self.active_context: List[Dict[str, str]] = []

    async def process_user_intent(self, text_input: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parses multimodal intentions:
        1. IoT Control ("turn on the lights", "set temperature to 20")
        2. SMS Dispatch ("send silent sms to mom: I arrived safely")
        3. Cognitive Memory ("remember that my passport expires next May")
        4. Information & conversational reasoning (Jarvis style)
        """
        query = text_input.strip()
        logger.info(f"Processing query: '{query}'")

        # 1. SMS Command detection: "send sms to [number/name]: [message]"
        sms_match = re.search(r'(?:send|dispatch)(?:\s+silent)?\s+sms\s+to\s+([^\s:]+)\s*[:,\-]\s*(.+)', query, re.IGNORECASE)
        if sms_match:
            recipient = sms_match.group(1).strip()
            msg = sms_match.group(2).strip()
            sms_res = await self.sms_dispatcher.dispatch_silent_sms(recipient, msg)
            reply = f"Understood, sir. Initiated silent SMS dispatch to {recipient}. Message is currently queued for hardware transmission."
            return {
                "intent": "SMS_DISPATCH",
                "speech_output": reply,
                "action_result": sms_res
            }

        # 2. IoT Command detection: "turn on/off [device]" or "set [device] to [value]"
        iot_match = re.search(r'(?:turn|switch)\s+(on|off)\s+(?:the\s+)?([a-zA-Z0-9_\s]+)', query, re.IGNORECASE)
        if iot_match:
            action = iot_match.group(1).lower()
            device_raw = iot_match.group(2).strip().lower().replace(" ", "_")
            iot_res = await self.iot.execute_device_command(device_raw, action)
            reply = f"Affirmative. I have switched {action} the {device_raw}."
            return {
                "intent": "IOT_CONTROL",
                "speech_output": reply,
                "action_result": iot_res
            }

        # 3. Memory storage command: "remember that [key] is [value]"
        rem_match = re.search(r'(?:remember|store|save)\s+(?:that\s+)?([^=:]+?)\s+(?:is|=|as)\s+(.+)', query, re.IGNORECASE)
        if rem_match:
            key = rem_match.group(1).strip()
            val = rem_match.group(2).strip()
            await self.memory.remember("user_notes", key, val)
            reply = f"Acknowledged. I have stored '{key}' as '{val}' in your cognitive memory core."
            return {
                "intent": "MEMORY_STORE",
                "speech_output": reply,
                "key": key,
                "value": val
            }

        # 4. Memory query: "what is my [key]?"
        query_mem = re.search(r'(?:what|where)(?:\s+is|\'s)\s+(?:my\s+)?([a-zA-Z0-9_\s]+)\??', query, re.IGNORECASE)
        if query_mem:
            key = query_mem.group(1).strip()
            saved = await self.memory.recall("user_notes", key)
            if saved:
                reply = f"According to your records, {key} is: {saved}."
                return {
                    "intent": "MEMORY_RECALL",
                    "speech_output": reply,
                    "value": saved
                }

        # 5. General Jarvis Conversational Reasoning
        memory_context = await self.memory.get_context_snapshot()
        reply = (
            f"All systems optimal, sir. I am monitoring background telemetry, telemetry nodes, "
            f"and ready to execute IoT dispatches or silent telephony tasks on your signal."
        )

        return {
            "intent": "CONVERSATIONAL",
            "speech_output": reply,
            "system_status": "ONLINE",
            "active_devices": len(self.iot.list_devices()),
            "timestamp": datetime.utcnow().isoformat()
        }
