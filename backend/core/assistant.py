"""
Jinny Core - Autonomous Cognitive Orchestrator & Multi-Tool Agent
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)

Replaces legacy RegEx parsing with Gemini Tool-Calling (Function Execution) loops.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from google import genai
from google.genai import types

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

        # تهيئة عميل Gemini إذا كان المفتاح متوفراً
        self.client: Optional[genai.Client] = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info("Gemini Agentic Engine initialized successfully.")
        else:
            logger.warning("GEMINI_API_KEY missing! Assistant will run in degraded mode.")

    def _build_tools_schema(self) -> List[types.Tool]:
        """
        تعريف الأدوات والـ Capabilities التي يستطيع الـ Agent استدعاؤها برمجياً.
        """
        sms_tool = types.FunctionDeclaration(
            name="dispatch_sms",
            description="Send a silent background SMS message to a phone number or contact through the host Android modem.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "recipient": types.Schema(type=types.Type.STRING, description="Target phone number or registered contact name."),
                    "message": types.Schema(type=types.Type.STRING, description="Text message content to dispatch."),
                    "priority": types.Schema(type=types.Type.INTEGER, description="1: Normal, 2: Urgent, 3: Critical emergency")
                },
                required=["recipient", "message"]
            )
        )

        iot_tool = types.FunctionDeclaration(
            name="control_iot_device",
            description="Control smart home devices, IoT switches, lights, climate ACs, locks, or send Wake-on-LAN packets.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "device_id": types.Schema(type=types.Type.STRING, description="Device identifier (e.g., living_room_light, ac_unit, smart_lock, workstation_pc)."),
                    "action": types.Schema(type=types.Type.STRING, description="Action to perform: 'on', 'off', 'lock', 'unlock', 'wake', etc."),
                    "temperature": types.Schema(type=types.Type.NUMBER, description="Target temperature in Celsius (optional, for climate/AC)."),
                    "brightness": types.Schema(type=types.Type.INTEGER, description="Brightness level 0-100 (optional, for lights).")
                },
                required=["device_id", "action"]
            )
        )

        memory_store_tool = types.FunctionDeclaration(
            name="store_user_memory",
            description="Store long-term cognitive facts, user preferences, habits, keys, and important notes.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "category": types.Schema(type=types.Type.STRING, description="Category of memory: 'user_notes', 'preferences', 'routines', etc."),
                    "key": types.Schema(type=types.Type.STRING, description="Unique key or label for the memory item."),
                    "value": types.Schema(type=types.Type.STRING, description="The detailed information or value to remember.")
                },
                required=["category", "key", "value"]
            )
        )

        memory_recall_tool = types.FunctionDeclaration(
            name="recall_user_memory",
            description="Retrieve stored knowledge, keys, user notes, and past remembered contexts.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "category": types.Schema(type=types.Type.STRING, description="Category of memory to query."),
                    "key": types.Schema(type=types.Type.STRING, description="Specific key to look up (optional).")
                },
                required=["category"]
            )
        )

        return [types.Tool(function_declarations=[sms_tool, iot_tool, memory_store_tool, memory_recall_tool])]

    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """توجيه استدعاء الأداة إلى الموديول المسؤول داخل النظام"""
        logger.info(f"Agent executing tool: {tool_name} with args: {args}")
        try:
            if tool_name == "dispatch_sms":
                return await self.sms_dispatcher.dispatch_silent_sms(
                    recipient=args["recipient"],
                    message=args["message"],
                    priority=args.get("priority", 1)
                )

            elif tool_name == "control_iot_device":
                params = {}
                if "temperature" in args:
                    params["temperature"] = args["temperature"]
                if "brightness" in args:
                    params["brightness"] = args["brightness"]
                return await self.iot.execute_device_command(
                    device_id=args["device_id"],
                    action=args["action"],
                    params=params
                )

            elif tool_name == "store_user_memory":
                await self.memory.remember(
                    category=args["category"],
                    key=args["key"],
                    value=args["value"]
                )
                return {"status": "success", "message": f"Stored {args['key']} in memory."}

            elif tool_name == "recall_user_memory":
                data = await self.memory.recall(
                    category=args["category"],
                    key=args.get("key")
                )
                return {"status": "success", "data": data}

            else:
                return {"status": "error", "message": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def process_user_intent(self, text_input: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        الدورة التفكيرية الكاملة للـ Agent:
        1. قراءة السياق من الذاكرة الحية.
        2. تمرير نص المستخدم ونواياه للـ LLM.
        3. استدعاء الـ Tools المناسبة وحل أي Dependencies.
        4. صياغة الرد النهائي بأسلوب Jarvis المهني المتوازن.
        """
        query = text_input.strip()
        logger.info(f"Agent received intent request: '{query}'")

        if not self.client:
            return {
                "intent": "FALLBACK_OFFLINE",
                "speech_output": "System online, but Gemini LLM engine is unconfigured. Please set GEMINI_API_KEY.",
                "action_result": None
            }

        # جلب سياق الذاكرة الأخير
        memory_context = await self.memory.get_context_snapshot()

        system_instruction = (
            "You are Jinny, a highly advanced autonomous Jarvis-grade AI operating core. "
            "You are engineered by Eng. Yousuf Albaz to manage IoT home infrastructure, persistent memory, "
            "and silent background cellular telemetry for Android. "
            "Maintain a sharp, polite, concise, and ultra-competent tone. "
            "Whenever the user asks you to control hardware, store memory, or dispatch SMS messages, "
            "always call the respective declared tool. Never hallucinate successful execution without calling the tool.\n\n"
            f"Active Memory Context:\n{memory_context}"
        )

        tools = self._build_tools_schema()

        try:
            # 1. المرحلة الأولى: استنتاج النوايا والأدوات
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tools,
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS
                )
            )

            # فحص إذا كان النموذج طلب استدعاء أداة (Function Call)
            executed_tools = []
            if response.function_calls:
                tool_results = []
                for call in response.function_calls:
                    result = await self._execute_tool(call.name, call.args)
                    executed_tools.append({"tool": call.name, "args": call.args, "result": result})
                    tool_results.append(
                        types.Part.from_function_response(
                            name=call.name,
                            response={"result": result}
                        )
                    )

                # 2. المرحلة الثانية: إعادة النتائج للنموذج لصياغة الرد الصوتي/النصي النهائي
                followup_response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=[
                        types.Content(role="user", parts=[types.Part.from_text(query)]),
                        types.Content(role="model", parts=response.candidates[0].content.parts),
                        types.Content(role="user", parts=tool_results)
                    ],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=settings.GEMINI_TEMPERATURE
                    )
                )

                final_text = followup_response.text or "Command executed successfully, sir."
                primary_intent = executed_tools[0]["tool"].upper() if executed_tools else "TOOL_EXECUTION"

                return {
                    "intent": primary_intent,
                    "speech_output": final_text,
                    "action_result": executed_tools,
                    "timestamp": datetime.utcnow().isoformat()
                }

            # محادثة عامة بدون الحاجة لأدوات
            return {
                "intent": "CONVERSATIONAL",
                "speech_output": response.text or "All systems nominal, sir.",
                "system_status": "ONLINE",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Inference pipeline failure: {e}", exc_info=True)
            return {
                "intent": "ERROR",
                "speech_output": f"Diagnostic anomaly detected during intent processing: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
