# Jinny Core 🤖⚡
### Autonomous Android Background Assistant & IoT Orchestrator

[![CI Pipeline](https://github.com/usufalbaz/Jinny-Assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/usufalbaz/Jinny-Assistant/actions)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Kotlin](https://img.shields.io/badge/Kotlin-Android-purple.svg)](https://kotlinlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Jinny Core is an enterprise-grade autonomous AI operating core engineered for resilient background execution on Android devices, synchronized with a high-throughput Python/FastAPI microservices orchestrator. Powered by Google Gemini Multi-Tool Function Calling, it delivers persistent vector semantic memory, hardware-level IoT automation (MQTT, Home Assistant & Wake-on-LAN), and silent cellular telephony dispatch with complete delivery lifecycle tracking.

---

## 🏗️ Architecture Overview

           +-------------------------------------------------------+
           |               Jinny Core Agent Brain                  |
           |     (FastAPI / Python + Gemini Function Calling)      |
           +---------------------------+---------------------------+
                                       |
             +-------------------------+-------------------------+
             |                         |                         |
    +--------v--------+       +--------v--------+       +--------v--------+
    | Semantic Memory |       |  IoT Controller |       | Telephony Gate  |
    | Vector Embeddings|      | MQTT / WoL / HA |       | (Priority Queue)|
    | (SQLite + NumPy)|       +-----------------+       +--------+--------+
    +-----------------+                                          |
                                                    (Authenticated WSS / WS)
                                                                 |
                                                        +--------v--------+
                                                        |  Android Daemon |
                                                        | (Foreground Svc)|
                                                        |  Timed WakeLock |
                                                        +-----------------+

---

## 🌟 Key Capabilities

### 1. Agentic Function Calling Brain (`core/assistant.py`)
* Replaces legacy regex pattern matching with **Gemini Tool-Calling (Function Execution) loops**.
* Dynamically resolves multimodal user intents into executable tool payloads (`dispatch_sms`, `control_iot_device`, `store_user_memory`, `recall_user_memory`).
* Enforces Jarvis-grade persona reasoning and contextual action feedback.

### 2. Cognitive Vector Semantic Memory (`core/memory.py`)
* Implements mathematical semantic similarity search using `text-embedding-004`.
* In-memory Cosine Similarity ranking via NumPy for lightning-fast context retrieval.
* Dynamic injection of ranked memories into active LLM system instructions.

### 3. Unified IoT & Hardware Orchestration (`core/iot_controller.py`)
* **Real-time MQTT:** Native asynchronous command and telemetry publishing via `paho-mqtt`.
* **Wake-on-LAN (WoL):** Low-level socket transmission of UDP Magic Packets to boot remote workstations.
* **Home Assistant REST Bridge:** Direct service dispatching for smart climate, lighting, and switches.

### 4. Resilient Telephony & SMS Dispatch (`core/sms_dispatcher.py`)
* Programmatic cellular SMS dispatching through the host Android modem without user prompt.
* E.164 phone number sanitization and priority-based task queuing (Critical / Urgent / Normal).
* Real-time delivery acknowledgment lifecycle (`pending` -> `queued_for_device` -> `dispatched` -> `failed`).

### 5. Battery-Conscious Android Daemon (`AssistantBackgroundService.kt`)
* Optimized Foreground Service utilizing **temporary timed wake-locks** exclusively during active task execution.
* Exponential-backoff reconnection strategy over bi-directional WebSockets to preserve network and battery.
* In-app dynamic configuration screen in Jetpack Compose for server host IP and API Key setup.

---

## 🔒 Security & Gateway Hardening

All REST and WebSocket endpoints are secured via the `X-Jinny-Api-Key` gateway header:
* `POST /api/assistant/interact` - Authenticated multi-tool agent inference.
* `POST /api/memory/search` - Semantic similarity vector query.
* `POST /api/sms/dispatch` - Cellular SMS queue dispatch.
* `GET /api/sms/tasks` - Live task queue and delivery status monitor.
* `WS /ws/android-bridge?token={KEY}` - Authenticated Android telemetry connection.

---

## 🚀 Quickstart & Setup

### 1. Backend Server Setup

    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    pytest tests/
    uvicorn main:app --host 0.0.0.0 --port 8080 --reload

### 2. Android Client Setup

1. Open `/android` in Android Studio.
2. Build and install the APK on an Android device running Android 9.0+.
3. Grant requested runtime permissions (SMS, Audio, Notifications).
4. Launch the app and enter your server IP address (e.g., `192.168.1.15:8080` for local WiFi or public IP) and your `X-Jinny-Api-Key`.
5. Tap **Start Daemon** to initiate background synchronization.

---

## 📄 License
Distributed under the MIT License. See LICENSE for details.
