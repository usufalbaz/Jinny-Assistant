"""
Jinny Core - IoT Automation & Direct Hardware Control
Engineered by Eng. Yousuf Albaz
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import httpx
from config import settings

logger = logging.getLogger("Jinny.IoT")

class IoTController:
    def __init__(self):
        self.device_registry: Dict[str, Dict[str, Any]] = {
            "living_room_light": {"type": "light", "state": "off", "brightness": 100, "protocol": "homeassistant"},
            "ac_unit": {"type": "climate", "state": "off", "temperature": 22, "mode": "cool", "protocol": "homeassistant"},
            "smart_lock": {"type": "lock", "state": "locked", "protocol": "mqtt"},
            "coffee_machine": {"type": "switch", "state": "off", "protocol": "mqtt"},
            "workstation_pc": {"type": "wol", "mac": "00:11:22:33:44:55", "protocol": "wol"}
        }

    async def execute_device_command(self, device_id: str, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        logger.info(f"Executing IoT Command: Device '{device_id}', Action '{action}', Params: {params}")

        if device_id not in self.device_registry:
            # Fuzzy match
            matched = None
            for d in self.device_registry:
                if d in device_id or device_id in d:
                    matched = d
                    break
            if matched:
                device_id = matched
            else:
                return {"status": "error", "message": f"Device '{device_id}' not found in registry"}

        device = self.device_registry[device_id]

        # Home Assistant REST Bridge if configured
        if settings.HOME_ASSISTANT_URL and settings.HOME_ASSISTANT_TOKEN:
            try:
                headers = {
                    "Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}",
                    "Content-Type": "application/json"
                }
                domain = device["type"]
                service = "turn_on" if action == "on" else "turn_off" if action == "off" else action
                url = f"{settings.HOME_ASSISTANT_URL}/api/services/{domain}/{service}"
                payload = {"entity_id": f"{domain}.{device_id}", **params}

                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    logger.info(f"Home Assistant Response: {resp.status_code}")
            except Exception as e:
                logger.warn(f"Home Assistant bridge error: {e}")

        # Update local registry state
        device["state"] = action
        if "brightness" in params:
            device["brightness"] = params["brightness"]
        if "temperature" in params:
            device["temperature"] = params["temperature"]

        return {
            "status": "success",
            "device_id": device_id,
            "new_state": device["state"],
            "device_info": device
        }

    def list_devices(self) -> Dict[str, Any]:
        return self.device_registry
