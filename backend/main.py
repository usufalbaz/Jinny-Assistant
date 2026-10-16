"""
Jinny Core - Production FastAPI Server & Jarvis Web HUD Entry Point
Architected & Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Security, status, Query
from fastapi.responses import Response, HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings
from core.memory import PersistentMemoryStore
from core.sms_dispatcher import SmsDispatcher
from core.iot_controller import IoTController
from core.assistant import JinnyAssistantCore
from core.voice_engine import NeuralVoiceEngine
from core.proactive_agent import ProactiveAutonomousAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s : %(message)s"
)
logger = logging.getLogger("Jinny.Server")

memory_store = PersistentMemoryStore()
sms_dispatcher = SmsDispatcher()
iot_controller = IoTController()
voice_engine = NeuralVoiceEngine()
assistant_core = JinnyAssistantCore(memory_store, sms_dispatcher, iot_controller)
proactive_agent = ProactiveAutonomousAgent(memory_store, iot_controller, sms_dispatcher)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Jinny Core Enterprise Subsystems...")
    await memory_store.initialize()
    await proactive_agent.start()
    logger.info(f"Jinny Core online and listening on {settings.HOST}:{settings.PORT}")
    yield
    logger.info("Gracefully shutting down Jinny Core services...")
    await proactive_agent.stop()
    logger.info("Jinny Core services stopped.")


app = FastAPI(
    title="Jinny Core AI Assistant Gateway",
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    if settings.DEBUG:
        return True
    if not api_key or api_key != settings.JINNY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Jinny API Key"
        )
    return True


class QueryRequest(BaseModel):
    query: str
    client_id: Optional[str] = "web_console"
    metadata: Optional[Dict[str, Any]] = None


class VoiceSynthesizeRequest(BaseModel):
    text: str
    voice: Optional[str] = None


class IoTCommandRequest(BaseModel):
    device_id: str
    action: str
    params: Optional[Dict[str, Any]] = None


# ----------------- The Holographic Jarvis Web HUD (Front-End) -----------------
@app.get("/", response_class=HTMLResponse)
async def jarvis_holographic_dashboard():
    """Returns the Stark Industries Holographic HUD Interface directly in browser."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JINNY CORE // STARK OS</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --cyan: #00f0ff;
                --cyan-glow: rgba(0, 240, 255, 0.4);
                --dark: #040814;
                --panel: rgba(8, 18, 38, 0.75);
                --red: #ff3366;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                background: radial-gradient(circle at center, #0a1428 0%, #030611 100%);
                color: #e2f1ff;
                font-family: 'Rajdhani', sans-serif;
                height: 100vh;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            header {
                padding: 18px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(0, 240, 255, 0.15);
                background: rgba(4, 8, 20, 0.8);
            }
            .logo {
                font-family: 'Orbitron', sans-serif;
                font-size: 24px;
                font-weight: 900;
                letter-spacing: 3px;
                color: var(--cyan);
                text-shadow: 0 0 15px var(--cyan-glow);
            }
            .status-pill {
                font-size: 13px;
                letter-spacing: 2px;
                padding: 6px 16px;
                border: 1px solid var(--cyan);
                border-radius: 20px;
                color: var(--cyan);
                box-shadow: 0 0 10px var(--cyan-glow);
                animation: pulse 2s infinite;
            }
            main {
                flex: 1;
                display: grid;
                grid-template-columns: 320px 1fr 340px;
                gap: 24px;
                padding: 24px;
                height: calc(100vh - 80px);
            }
            .hud-card {
                background: var(--panel);
                border: 1px solid rgba(0, 240, 255, 0.2);
                border-radius: 12px;
                padding: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.5);
                display: flex;
                flex-direction: column;
            }
            .card-title {
                font-family: 'Orbitron', sans-serif;
                font-size: 13px;
                letter-spacing: 2px;
                color: var(--cyan);
                margin-bottom: 16px;
                border-bottom: 1px dashed rgba(0, 240, 255, 0.2);
                padding-bottom: 8px;
            }
            /* Arc Reactor Core Center */
            .center-stage {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                position: relative;
            }
            .arc-reactor {
                width: 220px;
                height: 220px;
                border-radius: 50%;
                border: 2px solid var(--cyan);
                box-shadow: 0 0 40px var(--cyan-glow), inset 0 0 30px var(--cyan-glow);
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                cursor: pointer;
                transition: transform 0.3s;
            }
            .arc-reactor:hover { transform: scale(1.05); }
            .arc-reactor.active {
                border-color: var(--red);
                box-shadow: 0 0 60px rgba(255, 51, 102, 0.6);
            }
            .arc-inner-ring {
                width: 170px;
                height: 170px;
                border-radius: 50%;
                border: 2px dashed rgba(0, 240, 255, 0.6);
                animation: rotate 15s linear infinite;
            }
            .arc-core-text {
                position: absolute;
                font-family: 'Orbitron', sans-serif;
                font-size: 14px;
                font-weight: 700;
                color: #fff;
                letter-spacing: 2px;
                text-align: center;
            }
            .speech-readout {
                margin-top: 30px;
                width: 80%;
                max-width: 600px;
                text-align: center;
                font-size: 18px;
                color: #b8e2ff;
                min-height: 60px;
                line-height: 1.6;
                text-shadow: 0 0 8px rgba(0, 240, 255, 0.3);
            }
            /* Command input */
            .input-box {
                margin-top: 20px;
                width: 70%;
                display: flex;
                gap: 12px;
            }
            input[type="text"] {
                flex: 1;
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(0, 240, 255, 0.3);
                border-radius: 8px;
                padding: 12px 16px;
                color: #fff;
                font-family: 'Rajdhani', sans-serif;
                font-size: 16px;
                outline: none;
            }
            input[type="text"]:focus { border-color: var(--cyan); box-shadow: 0 0 10px var(--cyan-glow); }
            button.action-btn {
                background: rgba(0, 240, 255, 0.15);
                border: 1px solid var(--cyan);
                color: var(--cyan);
                font-family: 'Orbitron', sans-serif;
                font-size: 12px;
                letter-spacing: 1px;
                padding: 0 20px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
            }
            button.action-btn:hover { background: var(--cyan); color: #000; }
            /* Device List */
            .device-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
            .device-badge {
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 4px;
                background: rgba(0, 240, 255, 0.1);
                color: var(--cyan);
            }
            .log-terminal {
                font-family: monospace;
                font-size: 12px;
                color: #79a8d0;
                overflow-y: auto;
                flex: 1;
                line-height: 1.5;
            }
            @keyframes rotate { 100% { transform: rotate(360deg); } }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">⚡ JINNY // JARVIS CORE</div>
            <div class="status-pill" id="sys-status">● AUTONOMOUS ONLINE</div>
        </header>

        <main>
            <!-- Left: Smart Home & IoT Telemetry -->
            <div class="hud-card">
                <div class="card-title">HARDWARE NODES (IoT)</div>
                <div id="device-list">
                    <div class="device-item"><span>Living Room Light</span><span class="device-badge" id="dev-light">OFF</span></div>
                    <div class="device-item"><span>AC Climate Unit</span><span class="device-badge" id="dev-ac">22°C</span></div>
                    <div class="device-item"><span>Smart Lock</span><span class="device-badge" id="dev-lock">LOCKED</span></div>
                    <div class="device-item"><span>Workstation PC</span><span class="device-badge" id="dev-pc">WOL READY</span></div>
                </div>
            </div>

            <!-- Center: Interactive Arc Reactor & Voice Visualizer -->
            <div class="center-stage">
                <div class="arc-reactor" id="reactor-orb" onclick="toggleVoiceListening()">
                    <div class="arc-inner-ring"></div>
                    <div class="arc-core-text" id="core-state">CLICK TO<br>SPEAK</div>
                </div>

                <div class="speech-readout" id="readout">
                    "All systems optimal, sir. Microphone and neural voice channels are ready."
                </div>

                <div class="input-box">
                    <input type="text" id="cmd-input" placeholder="Type an order or click the Arc Reactor to speak..." onkeypress="if(event.key==='Enter') sendCommand()">
                    <button class="action-btn" onclick="sendCommand()">TRANSMIT</button>
                </div>
            </div>

            <!-- Right: Neural Logs & Telemetry -->
            <div class="hud-card">
                <div class="card-title">DIAGNOSTIC TELEMETRY</div>
                <div class="log-terminal" id="term-logs">
                    [SYSTEM BOOT] Jinny Core v3.0 Online.<br>
                    [MEMORY] Semantic vector SQLite linked.<br>
                    [VOICE] Edge Neural TTS loaded.<br>
                    [AWAITING] Standing by for instructions...
                </div>
            </div>
        </main>

        <audio id="tts-player" autoplay></audio>

        <script>
            const API_KEY = "jinny_live_sec_prod_9948201847192847";
            const readout = document.getElementById("readout");
            const coreText = document.getElementById("core-state");
            const orb = document.getElementById("reactor-orb");
            const logs = document.getElementById("term-logs");
            const player = document.getElementById("tts-player");

            function log(msg) {
                const now = new Date().toLocaleTimeString();
                logs.innerHTML += `<br>[${now}] ${msg}`;
                logs.scrollTop = logs.scrollHeight;
            }

            // Speak response aloud using Jinny's Neural TTS Endpoint
            async function speakOut(text) {
                try {
                    log("Synthesizing neural voice output...");
                    const res = await fetch("/api/voice/synthesize", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-Jinny-Api-Key": API_KEY },
                        body: JSON.stringify({ text: text })
                    });
                    if (res.ok) {
                        const blob = await res.blob();
                        player.src = URL.createObjectURL(blob);
                        player.play();
                    } else {
                        // Fallback to browser built-in speech
                        const utter = new SpeechSynthesisUtterance(text);
                        utter.pitch = 0.9;
                        window.speechSynthesis.speak(utter);
                    }
                } catch(e) {
                    console.error("Audio playback error:", e);
                }
            }

            // Transmit User Order to AI Agent Brain
            async function processQuery(queryText) {
                if(!queryText.trim()) return;
                readout.innerText = `Processing: "${queryText}"...`;
                log(`QUERY: "${queryText}"`);

                try {
                    const res = await fetch("/api/assistant/interact", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-Jinny-Api-Key": API_KEY },
                        body: JSON.stringify({ query: queryText })
                    });
                    const data = await res.json();
                    const reply = data.speech_output || "Command processed, sir.";
                    readout.innerText = `"${reply}"`;
                    log(`JINNY: ${reply}`);
                    speakOut(reply);
                    updateDevices();
                } catch(e) {
                    readout.innerText = "Connection anomaly encountered.";
                    log(`ERROR: ${e.message}`);
                }
            }

            function sendCommand() {
                const input = document.getElementById("cmd-input");
                processQuery(input.value);
                input.value = "";
            }

            // Voice Recognition from Laptop Microphone
            let recognition;
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRec();
                recognition.continuous = false;
                recognition.lang = 'en-US';

                recognition.onstart = () => {
                    orb.classList.add("active");
                    coreText.innerHTML = "LISTENING...";
                    log("Microphone engaged. Speak your command.");
                };
                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    processQuery(transcript);
                };
                recognition.onend = () => {
                    orb.classList.remove("active");
                    coreText.innerHTML = "CLICK TO<br>SPEAK";
                };
            }

            function toggleVoiceListening() {
                if (recognition) {
                    recognition.start();
                } else {
                    alert("Speech recognition is not supported in this browser. Please use Chrome.");
                }
            }

            async function updateDevices() {
                try {
                    const res = await fetch("/api/iot/devices", {
                        headers: { "X-Jinny-Api-Key": API_KEY }
                    });
                    const devices = await res.json();
                    if(devices.living_room_light) document.getElementById("dev-light").innerText = devices.living_room_light.state.toUpperCase();
                    if(devices.ac_unit) document.getElementById("dev-ac").innerText = `${devices.ac_unit.temperature}°C`;
                    if(devices.smart_lock) document.getElementById("dev-lock").innerText = devices.smart_lock.state.toUpperCase();
                } catch(e) {}
            }
            setInterval(updateDevices, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ----------------- Existing API Endpoints -----------------
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "system": "Jinny Core",
        "version": settings.VERSION,
        "author": "Eng. Yousuf Albaz (AI & Systems Engineer)"
    }


@app.post("/api/assistant/interact", dependencies=[Depends(verify_api_key)])
async def interact_with_assistant(req: QueryRequest):
    try:
        response = await assistant_core.process_user_intent(req.query, req.metadata)
        return response
    except Exception as e:
        logger.error(f"Inference gateway error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/synthesize", dependencies=[Depends(verify_api_key)])
async def synthesize_voice(req: VoiceSynthesizeRequest):
    try:
        audio_bytes = await voice_engine.synthesize_speech(req.text, req.voice)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"Voice synthesis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/iot/devices", dependencies=[Depends(verify_api_key)])
async def list_iot_devices():
    return iot_controller.list_devices()


@app.post("/api/iot/execute", dependencies=[Depends(verify_api_key)])
async def execute_iot_command(req: IoTCommandRequest):
    return await iot_controller.execute_device_command(req.device_id, req.action, req.params)
