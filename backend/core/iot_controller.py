"""
Jinny Core - IoT Automation & Hardware Orchestration Subsystem
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)

Real hardware abstraction layer:
- Home Assistant REST Service execution
- Real-time MQTT telemetry and command publishing via paho-mqtt
- Standard UDP Wake-on-LAN (WoL) Magic Packet dispatcher
"""

import logging
import socket
import json
import asyncio
from typing import Dict, Any, List, Optional
import httpx
import paho.mqtt.publish as publish

from config import settings

logger = logging.getLogger("Jinny.IoT")


class IoTController:
    def __init__(self):
        # سجل الأجهزة المدعومة وأنواع البروتوكولات الخاصة بها
        self.device_registry: Dict[str, Dict[str, Any]] = {
            "living_room_light": {"type": "light", "state": "off", "brightness": 100, "protocol": "homeassistant"},
            "ac_unit": {"type": "climate", "state": "off", "temperature": 22, "mode": "cool", "protocol": "homeassistant"},
            "smart_lock": {"type": "lock", "state": "locked", "protocol": "mqtt", "topic": "jinny/lock/set"},
            "coffee_machine": {"type": "switch", "state": "off", "protocol": "mqtt", "topic": "jinny/coffee/set"},
            "workstation_pc": {"type": "wol", "mac": "00:11:22:33:44:55", "protocol": "wol"}
        }

    @staticmethod
    def _send_wol_packet(mac_address: str, broadcast_ip: str = settings.WOL_BROADCAST_IP, port: int = settings.WOL_PORT) -> bool:
        """
        إرسال Magic Packet القياسي عبر UDP لإيقاظ الكمبيوتر المغلق (Wake-on-LAN)
        """
        try:
            # تنظيف صيغة الـ MAC Address
            clean_mac = mac_address.replace(":", "").replace("-", "").replace(".", "")
            if len(clean_mac) != 12:
                raise ValueError(f"Invalid MAC address format: {mac_address}")

            # تكوين الـ Magic Packet: 6 بايتات FF متبوعة بـ MAC مكرر 16 مرة
            payload = bytes.fromhex("FF" * 6 + clean_mac * 16)

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(payload, (broadcast_ip, port))

            logger.info(f"Wake-on-LAN Magic Packet broadcasted to {mac_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to transmit WoL packet: {e}")
            return False

    async def _send_mqtt_command(self, topic: str, payload: Dict[str, Any]) -> bool:
        """
        نشر أمر حقيقي لوسيط MQTT بشكل غير متزامن (Asynchronous)
        """
        try:
            auth = None
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                auth = {"username": settings.MQTT_USERNAME, "password": settings.MQTT_PASSWORD}

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: publish.single(
                    topic=topic,
                    payload=json.dumps(payload),
                    hostname=settings.MQTT_BROKER_HOST,
                    port=settings.MQTT_BROKER_PORT,
                    auth=auth,
                    keepalive=settings.MQTT_KEEPALIVE
                )
            )
            logger.info(f"MQTT payload dispatched to topic '{topic}': {payload}")
            return True
        except Exception as e:
            logger.warning(f"MQTT dispatch failed (Broker unreachable?): {e}")
            return False

    async def _call_home_assistant(self, domain: str, service: str, entity_id: str, params: Dict[str, Any]) -> bool:
        """
        استدعاء خدمات Home Assistant عبر الـ REST API الرسمي
        """
        if not settings.HOME_ASSISTANT_URL or not settings.HOME_ASSISTANT_TOKEN:
            logger.warning("Home Assistant URL or Token not configured in settings.")
            return False

        headers = {
            "Authorization": f"Bearer {settings.HOME_ASSISTANT_TOKEN}",
            "Content-Type": "application/json"
        }
        url = f"{settings.HOME_ASSISTANT_URL.rstrip('/')}/api/services/{domain}/{service}"
        payload = {"entity_id": entity_id, **params}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code in [200, 201]:
                    logger.info(f"Home Assistant command executed successfully: {service} on {entity_id}")
                    return True
                else:
                    logger.error(f"Home Assistant API returned error: {resp.status_code} - {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"Home Assistant connection failure: {e}")
            return False

    async def execute_device_command(self, device_id: str, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        تنفيذ الأوامر الذكية وتحويلها إلى البروتوكول المناسب للجهاز
        """
        params = params or {}
        logger.info(f"Executing IoT Command: Device='{device_id}', Action='{action}', Params={params}")

        # البحث المطابق أو التقريبي عن الجهاز
        target_id = None
        for d in self.device_registry:
            if d == device_id or d in device_id or device_id in d:
                target_id = d
                break

        if not target_id:
            return {"status": "error", "message": f"Device '{device_id}' not found in registry."}

        device = self.device_registry[target_id]
        protocol = device.get("protocol", "homeassistant")
        success = False

        # 1. بروتوكول Wake-on-LAN
        if protocol == "wol" or action.lower() in ["wake", "boot", "wol"]:
            mac = device.get("mac", "00:11:22:33:44:55")
            success = self._send_wol_packet(mac)

        # 2. بروتوكول MQTT
        elif protocol == "mqtt":
            topic = device.get("topic", f"{settings.MQTT_BASE_TOPIC}/{target_id}/set")
            payload = {"state": action, **params}
            success = await self._send_mqtt_command(topic, payload)

        # 3. بروتوكول Home Assistant
        elif protocol == "homeassistant":
            domain = device["type"]
            service = "turn_on" if action.lower() == "on" else "turn_off" if action.lower() == "off" else action.lower()
            entity_id = f"{domain}.{target_id}"
            success = await self._call_home_assistant(domain, service, entity_id, params)

        # تحديث الحالة محلياً
        device["state"] = action
        if "brightness" in params:
            device["brightness"] = params["brightness"]
        if "temperature" in params:
            device["temperature"] = params["temperature"]

        return {
            "status": "success" if success else "executed_locally",
            "device_id": target_id,
            "action": action,
            "new_state": device["state"],
            "protocol_dispatched": protocol
        }

    def list_devices(self) -> Dict[str, Any]:
        return self.device_registry
