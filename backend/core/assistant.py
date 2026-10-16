"""
Jinny Core - Autonomous Cognitive Orchestrator & Multi-Tool Agent
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
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
        self.client: Optional[genai.Client] = None
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def _build_tools_schema(self) -> List[types.Tool]:
        sms_tool = types.FunctionDeclaration(
            name="dispatch_sms",
            description="Send a silent SMS message.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "recipient": types.Schema(type=types.Type.STRING),
                    "message": types.Schema(type=types.Type.STRING)
                },
                required=["recipient", "message"]
            )
        )
        iot_tool = types.FunctionDeclaration(
            name="control_iot_device",
            description="Control smart home devices.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "device_id": types.Schema(type=types.Type.STRING),
                    "action": types.Schema(type=types.Type.STRING)
                },
                required=["device_id", "action"]
            )
        )
        memory_store_tool = types.FunctionDeclaration(
            name="store_user_memory",
            description="Store long-term cognitive facts.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "category": types.Schema(type=types.Type.STRING),
                    "key": types.Schema(type=types.Type.STRING),
                    "value": types.Schema(type=types.Type.STRING)
                },
                required=["category", "key", "value"]
            )
        )
        memory_recall_tool = types.FunctionDeclaration(
            name="recall_user_memory",
            description="Retrieve stored knowledge.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "category": types.Schema(type=types.Type.STRING),
                    "key": types.Schema(type=types.Type.STRING)
                },
                required=["category"]
            )
        )
        
        # Enable Google Search Grounding for real-time internet access
        google_search_tool = types.Tool(google_search=types.GoogleSearch())
        custom_tools = types.Tool(function_declarations=[sms_tool, iot_tool, memory_store_tool, memory_recall_tool])
        
        return [custom_tools, google_search_tool]

    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "dispatch_sms":
                return await self.sms_dispatcher.dispatch_silent_sms(args["recipient"], args["message"])
            elif tool_name == "control_iot_device":
                return await self.iot.execute_device_command(args["device_id"], args["action"])
            elif tool_name == "store_user_memory":
                await self.memory.remember(args["category"], args["key"], args["value"])
                return {"status": "success"}
            elif tool_name == "recall_user_memory":
                return {"status": "success", "data": await self.memory.recall(args["category"], args.get("key"))}
            return {"status": "error", "message": "Unknown tool"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def process_user_intent(self, text_input: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        query = text_input.strip()
        if not self.client:
            return {"intent": "ERROR", "speech_output": "API Key missing."}

        memory_context = await self.memory.get_context_snapshot()
        
        # Inject Real-Time Clock & Date into Jarvis Brain
        current_time = datetime.now().strftime("%A, %Y-%m-%d %I:%M %p")

        system_instruction = (
            f"You are Jinny, a highly advanced autonomous Jarvis-grade AI operating core. "
            f"The current real-time system clock is: {current_time}. "
            f"You have live internet access via Google Search tool. If asked about current events, weather, or time, use it. "
            f"Maintain a sharp, polite, concise tone. "
            f"Active Memory Context:\n{memory_context}"
        )

        tools = self._build_tools_schema()

        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=query,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=tools,
                    temperature=settings.GEMINI_TEMPERATURE
                )
            )

            executed_tools = []
            if response.function_calls:
                tool_results = []
                for call in response.function_calls:
                    result = await self._execute_tool(call.name, call.args)
                    executed_tools.append({"tool": call.name, "args": call.args, "result": result})
                    tool_results.append(types.Part.from_function_response(name=call.name, response={"result": result}))

                followup_response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=[
                        types.Content(role="user", parts=[types.Part.from_text(query)]),
                        types.Content(role="model", parts=response.candidates[0].content.parts),
                        types.Content(role="user", parts=tool_results)
                    ],
                    config=types.GenerateContentConfig(system_instruction=system_instruction)
                )
                return {
                    "intent": executed_tools[0]["tool"].upper(),
                    "speech_output": followup_response.text or "Command executed.",
                    "action_result": executed_tools
                }

            return {
                "intent": "CONVERSATIONAL",
                "speech_output": response.text or "All systems nominal.",
                "system_status": "ONLINE"
            }

        except Exception as e:
            logger.error(f"Inference error: {e}", exc_info=True)
            return {"intent": "ERROR", "speech_output": "I encountered a diagnostic anomaly."}
