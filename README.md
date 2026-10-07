# Jinny Core 🤖⚡
### Autonomous Android Background Assistant & IoT Orchestrator

[![CI Pipeline](https://github.com/usufalbaz/Jinny-Assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/usufalbaz/Jinny-Assistant/actions)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Kotlin](https://img.shields.io/badge/Kotlin-Android-purple.svg)](https://kotlinlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Production-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Jinny Core is an autonomous AI assistant engineered for resilient 24/7 background execution on Android devices, synchronized with a high-throughput Python/FastAPI microservices orchestrator. It delivers persistent cognitive memory, direct smart-home IoT automation (MQTT & Home Assistant), and silent telephony SMS dispatch without user interruption.

---

## 🏗️ Architecture Overview

    +-----------------------------+
    |      Jinny Core Brain       |
    |       (FastAPI / Python)    |
    +--------------+--------------+
                   |
         +---------+---------+
         |                   |
    +----v-----+       +-----v-----+       +---------------------+
    | Cognitive|       |    IoT    |       | Silent SMS Dispatch |
    |  Memory  |       |Automation |       |  (WebSocket Bridge) |
    | (SQLite) |       |  (MQTT)   |       +----------+----------+
    +----------+       +-----------+                  |
                                           +----------v----------+
                                           |  Android Daemon     |
                                           | (Foreground Service)|
                                           +---------------------+

---

## 🌟 Key Capabilities

1. Persistent Cognitive Memory (core/memory.py):
   * Stores user preferences, routines, and contextual facts in long-term structured SQLite storage.
   * Dynamic memory retrieval and context injection into conversational inference loops.

2. Silent Telephony & SMS Dispatch (core/sms_dispatcher.py):
   * Dispatches programmatic SMS messages directly through the host Android device cellular modem silently in the background.
   * Handles offline message queuing and automatic flushing upon reconnection.

3. Direct IoT Hardware Control (core/iot_controller.py):
   * Unified hardware abstraction supporting Home Assistant REST APIs, MQTT brokers, and Wake-on-LAN (WoL).
   * Natural language intent parsing for environmental controls and smart devices.

4. Resilient Android Daemon (AssistantBackgroundService.kt):
   * 24/7 background persistence via Android Foreground Service and partial CPU wake-locks.
   * Bi-directional WebSocket telemetry stream with automatic exponential-backoff reconnect loops.

---

## 🚀 Quickstart & Setup

### 1. Backend Server Setup

    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt pytest
    pytest tests/
    uvicorn main:app --host 0.0.0.0 --port 8080 --reload

### 2. Android Daemon Setup

1. Open `/android` in Android Studio.
2. Configure server IP endpoint in `AssistantBackgroundService.kt` (defaults to `10.0.2.2:8080` for emulator).
3. Build and install the APK on an Android device running Android 9.0+.
4. Grant the requested SMS and Audio runtime permissions upon first launch.

---

## 📄 License
Distributed under the MIT License. See LICENSE for details.
