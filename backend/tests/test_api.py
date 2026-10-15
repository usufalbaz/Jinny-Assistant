"""
Jinny Core - Gateway & API Automated Test Suite
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# إضافة مجلد backend إلى مسار بايثون
sys.path.append(str(Path(__file__).parent.parent))

from main import app
from config import settings

AUTH_HEADERS = {
    settings.API_KEY_HEADER: settings.JINNY_API_KEY
}


def test_health_check_open_endpoint():
    """اختبار نقطة فحص الحالة (مفتوحة بدون مفتاح أمان)"""
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["system"] == "Jinny Core"


def test_protected_endpoints_reject_unauthorized():
    """اختبار أن النظام يرفض أي طلب بدون مفتاح أمان بكود 401"""
    with TestClient(app) as client:
        # تجربة طلب بدون هيدر الأمان
        response = client.get("/api/iot/devices")
        assert response.status_code == 401

        # تجربة طلب بمفتاح أمان خاطئ
        response = client.get("/api/iot/devices", headers={settings.API_KEY_HEADER: "wrong_fake_key"})
        assert response.status_code == 401


def test_list_iot_devices_authorized():
    """اختبار جلب أجهزة الـ IoT بعد تمرير مفتاح الأمان الصحيح"""
    with TestClient(app) as client:
        response = client.get("/api/iot/devices", headers=AUTH_HEADERS)
        assert response.status_code == 200
        devices = response.json()
        assert "living_room_light" in devices
        assert "ac_unit" in devices


def test_assistant_interaction_authorized():
    """اختبار التفاعل مع المساعد الذكي مع تمرير مفتاح الأمان"""
    with TestClient(app) as client:
        payload = {"query": "Status report, Jinny"}
        response = client.post("/api/assistant/interact", json=payload, headers=AUTH_HEADERS)
        assert response.status_code == 200
        res_json = response.json()
        assert "intent" in res_json
        assert "speech_output" in res_json
