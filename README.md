# Jinny Core 🤖⚡
### Autonomous Jarvis-Inspired AI Assistant & IoT Orchestrator for Android

**Jinny Core** is an enterprise-grade, Jarvis-inspired autonomous AI assistant engineered for background execution on Android devices, coupled with a high-throughput Python/FastAPI microservices backend. It delivers persistent cognitive memory, direct IoT smart-home control (MQTT & Home Assistant), and silent telephony SMS dispatch without user interruption.

---

## 🏗️ Architecture Overview

```
                      +-----------------------------+
                      |      Jinny Core Brain       |
                      |       (FastAPI / Python)    |
                      +--------------+--------------+
                                     |
           +-------------------------+-------------------------+
           |                         |                         |
+----------v----------+   +----------v----------+   +----------v----------+
|  Cognitive Memory   |   |   IoT Automation    |   | Silent SMS Dispatch |
| (Async SQLite / DB) |   | (MQTT / Home Assist)|   | (WebSocket Bridge)  |
+---------------------+   +---------------------+   +----------+----------+
                                                               |
                                                    +----------v----------+
                                                    |  Android Daemon     |
                                                    | (Foreground Service)|
                                                    +---------------------+
```

---

## 🌟 Key Capabilities

1. **Persistent Cognitive Memory (`core/memory.py`)**:
   - Stores user preferences, routines, keys, and personal facts in long-term structured storage with confidence scores.
   - Dynamic memory retrieval and context injection into conversational turns.

2. **Silent Telephony & SMS Dispatch (`core/sms_dispatcher.py`)**:
   - Dispatches programmatic SMS messages directly through the host Android phone's cellular modem silently in the background.
   - Handles offline queues and auto-flushes tasks upon device reconnection.

3. **Direct IoT Hardware Control (`core/iot_controller.py`)**:
   - Unified interface supporting Home Assistant REST APIs, MQTT brokers, and Wake-on-LAN (WoL).
   - Natural language intent parsing: *"Turn off the living room lights"*, *"Set AC to 21 degrees"*.

4. **Resilient Android Daemon (`AssistantBackgroundService.kt`)**:
   - 24/7 background persistence via Android Foreground Service and partial CPU wake-locks.
   - Low-latency bi-directional WebSocket telemetry stream with automatic reconnect loops.

---

## 🚀 Quick Start Guide

### 1. Backend Setup (Python 3.10+)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### 2. Android App Setup

1. Open `/android` in **Android Studio**.
2. Configure your server IP in `AssistantBackgroundService.kt` (defaults to `10.0.2.2:8080` for emulator).
3. Build and install the APK on an Android device running Android 9.0 to 14+.
4. Grant the requested **SMS** and **Audio** permissions upon first launch.

---

## 👨‍💻 Engineering & Development

- **Lead Architect & Systems Engineer**: **Eng. Yousuf Albaz** (AI & Systems Engineer)
- **Repository**: [github.com/usufalbaz/Jinny-Assistant](https://github.com/usufalbaz/Jinny-Assistant)

---

## 📄 License
MIT License. Engineered by Eng. Yousuf Albaz.
