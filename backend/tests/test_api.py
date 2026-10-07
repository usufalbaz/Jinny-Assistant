import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
sys.path.append(str(Path(__file__).parent.parent))

from main import app

def test_health_check():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["system"] == "Jinny Core"

def test_list_iot_devices():
    with TestClient(app) as client:
        response = client.get("/api/iot/devices")
        assert response.status_code == 200
        devices = response.json()
        assert "living_room_light" in devices
        assert "ac_unit" in devices

def test_assistant_interaction_conversational():
    with TestClient(app) as client:
        payload = {"query": "Status report, Jinny"}
        response = client.post("/api/assistant/interact", json=payload)
        assert response.status_code == 200
        res_json = response.json()
        assert res_json["intent"] == "CONVERSATIONAL"
        assert res_json["system_status"] == "ONLINE"
