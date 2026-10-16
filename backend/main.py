"""
Jinny Core - Production FastAPI Server & Stark Industries Interactive HUD
Architected & Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
"""

import logging
import os
import json
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Security, status, Query
from fastapi.responses import Response, HTMLResponse
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai

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


class ApiKeyUpdateRequest(BaseModel):
    gemini_api_key: str


# ----------------- Dynamic Settings Endpoint -----------------
@app.post("/api/settings/gemini-key")
async def update_gemini_api_key(req: ApiKeyUpdateRequest):
    """Dynamically set and activate Gemini API Key from the web dashboard."""
    key = req.gemini_api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")

    settings.GEMINI_API_KEY = key
    assistant_core.client = genai.Client(api_key=key)
    memory_store.client = genai.Client(api_key=key)

    # Persist key to .env file
    try:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        with open(env_path, "w") as f:
            f.write(f"GEMINI_API_KEY={key}\n")
    except Exception as e:
        logger.warning(f"Could not write .env file: {e}")

    logger.info("Gemini API Key dynamically configured and activated.")
    return {"status": "success", "message": "Gemini AI Core online and fully activated!"}


# ----------------- The Holographic Jarvis Web HUD -----------------
@app.get("/", response_class=HTMLResponse)
async def jarvis_holographic_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JINNY // JARVIS CORE</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --cyan: #00f0ff;
                --cyan-glow: rgba(0, 240, 255, 0.45);
                --dark: #040814;
                --panel: rgba(8, 18, 38, 0.85);
                --red: #ff3366;
                --green: #00ff88;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
                background: radial-gradient(circle at center, #0d1a33 0%, #030611 100%);
                color: #e2f1ff;
                font-family: 'Rajdhani', sans-serif;
                height: 100vh;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
            header {
                padding: 16px 36px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(0, 240, 255, 0.2);
                background: rgba(4, 8, 20, 0.9);
            }
            .logo {
                font-family: 'Orbitron', sans-serif;
                font-size: 24px;
                font-weight: 900;
                letter-spacing: 3px;
                color: var(--cyan);
                text-shadow: 0 0 15px var(--cyan-glow);
            }
            .header-controls { display: flex; gap: 14px; align-items: center; }
            .status-pill {
                font-size: 12px;
                letter-spacing: 2px;
                padding: 6px 14px;
                border: 1px solid var(--cyan);
                border-radius: 20px;
                color: var(--cyan);
                box-shadow: 0 0 10px var(--cyan-glow);
            }
            .settings-btn {
                background: rgba(0, 240, 255, 0.1);
                border: 1px solid var(--cyan);
                color: var(--cyan);
                padding: 6px 12px;
                border-radius: 8px;
                cursor: pointer;
                font-family: 'Orbitron', sans-serif;
                font-size: 13px;
                transition: all 0.2s;
            }
            .settings-btn:hover { background: var(--cyan); color: #000; }
            main {
                flex: 1;
                display: grid;
                grid-template-columns: 340px 1fr 340px;
                gap: 20px;
                padding: 20px;
                height: calc(100vh - 75px);
            }
            .hud-card {
                background: var(--panel);
                border: 1px solid rgba(0, 240, 255, 0.25);
                border-radius: 12px;
                padding: 20px;
                backdrop-filter: blur(12px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.6);
                display: flex;
                flex-direction: column;
            }
            .card-title {
                font-family: 'Orbitron', sans-serif;
                font-size: 13px;
                letter-spacing: 2px;
                color: var(--cyan);
                margin-bottom: 16px;
                border-bottom: 1px dashed rgba(0, 240, 255, 0.25);
                padding-bottom: 8px;
            }
            /* Interactive Device Cards */
            .device-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px;
                margin-bottom: 10px;
                background: rgba(0, 240, 255, 0.04);
                border: 1px solid rgba(0, 240, 255, 0.12);
                border-radius: 8px;
            }
            .device-name { font-weight: 700; font-size: 15px; }
            .toggle-btn {
                padding: 5px 14px;
                font-family: 'Orbitron', sans-serif;
                font-size: 11px;
                border-radius: 6px;
                cursor: pointer;
                border: 1px solid;
                transition: all 0.2s;
            }
            .toggle-btn.on { background: var(--cyan); color: #000; border-color: var(--cyan); box-shadow: 0 0 10px var(--cyan-glow); }
            .toggle-btn.off { background: transparent; color: #8899aa; border-color: #445566; }
            .climate-ctrl { display: flex; gap: 8px; align-items: center; }
            .ctrl-btn { background: rgba(0,240,255,0.15); border: 1px solid var(--cyan); color: #fff; width: 28px; height: 28px; border-radius: 4px; cursor: pointer; font-weight: bold; }
            /* Arc Reactor Center */
            .center-stage {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                position: relative;
            }
            .arc-reactor {
                width: 230px;
                height: 230px;
                border-radius: 50%;
                border: 3px solid var(--cyan);
                box-shadow: 0 0 50px var(--cyan-glow), inset 0 0 35px var(--cyan-glow);
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                cursor: pointer;
                transition: all 0.3s;
            }
            .arc-reactor:hover { transform: scale(1.04); }
            .arc-reactor.active { border-color: var(--red); box-shadow: 0 0 70px rgba(255, 51, 102, 0.7); }
            .arc-inner-ring {
                width: 180px;
                height: 180px;
                border-radius: 50%;
                border: 2px dashed rgba(0, 240, 255, 0.7);
                animation: rotate 12s linear infinite;
            }
            .arc-core-text {
                position: absolute;
                font-family: 'Orbitron', sans-serif;
                font-size: 13px;
                font-weight: 700;
                color: #fff;
                letter-spacing: 2px;
                text-align: center;
            }
            #wave-canvas { width: 300px; height: 60px; margin-top: 20px; }
            .speech-readout {
                margin-top: 15px;
                width: 85%;
                max-width: 650px;
                text-align: center;
                font-size: 19px;
                color: #cce7ff;
                min-height: 55px;
                line-height: 1.5;
                text-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
            }
            .input-box { margin-top: 20px; width: 80%; display: flex; gap: 12px; }
            input[type="text"] {
                flex: 1;
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(0, 240, 255, 0.3);
                border-radius: 8px;
                padding: 12px 18px;
                color: #fff;
                font-family: 'Rajdhani', sans-serif;
                font-size: 16px;
                outline: none;
            }
            input[type="text"]:focus { border-color: var(--cyan); box-shadow: 0 0 12px var(--cyan-glow); }
            .action-btn {
                background: rgba(0, 240, 255, 0.18);
                border: 1px solid var(--cyan);
                color: var(--cyan);
                font-family: 'Orbitron', sans-serif;
                font-size: 12px;
                letter-spacing: 1px;
                padding: 0 24px;
                border-radius: 8px;
                cursor: pointer;
            }
            .action-btn:hover { background: var(--cyan); color: #000; }
            .log-terminal { font-family: monospace; font-size: 12px; color: #79a8d0; overflow-y: auto; flex: 1; line-height: 1.6; }
            /* Modal */
            .modal-overlay {
                display: none;
                position: fixed;
                top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0,0,0,0.85);
                backdrop-filter: blur(8px);
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }
            .modal-content {
                background: #081226;
                border: 2px solid var(--cyan);
                box-shadow: 0 0 40px var(--cyan-glow);
                border-radius: 12px;
                padding: 30px;
                width: 90%;
                max-width: 480px;
            }
            @keyframes rotate { 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">⚡ JINNY // JARVIS CORE</div>
            <div class="header-controls">
                <div class="status-pill" id="sys-status">● SYSTEM STANDBY</div>
                <button class="settings-btn" onclick="openModal()">⚙️ AI KEY</button>
            </div>
        </header>

        <main>
            <!-- Left: Interactive IoT Hardware Controls -->
            <div class="hud-card">
                <div class="card-title">SMART HARDWARE SWITCHES</div>

                <div class="device-row">
                    <div><div class="device-name">Living Room Light</div><small style="color:#6e859d">HomeAssistant Bridge</small></div>
                    <button class="toggle-btn off" id="btn-light" onclick="toggleDevice('living_room_light')">OFF</button>
                </div>

                <div class="device-row">
                    <div><div class="device-name">Climate AC Unit</div><small style="color:#6e859d" id="temp-display">22°C</small></div>
                    <div class="climate-ctrl">
                        <button class="ctrl-btn" onclick="adjustTemp(-1)">-</button>
                        <button class="ctrl-btn" onclick="adjustTemp(+1)">+</button>
                    </div>
                </div>

                <div class="device-row">
                    <div><div class="device-name">Smart Lock</div><small style="color:#6e859d">MQTT Realtime</small></div>
                    <button class="toggle-btn on" id="btn-lock" onclick="toggleLock()">LOCKED</button>
                </div>

                <div class="device-row">
                    <div><div class="device-name">Workstation PC</div><small style="color:#6e859d">Wake-on-LAN</small></div>
                    <button class="toggle-btn off" onclick="wakePc()">WAKE PC</button>
                </div>
            </div>

            <!-- Center: Arc Reactor & Voice Wave -->
            <div class="center-stage">
                <div class="arc-reactor" id="reactor-orb" onclick="toggleVoiceListening()">
                    <div class="arc-inner-ring"></div>
                    <div class="arc-core-text" id="core-state">CLICK TO<br>SPEAK</div>
                </div>

                <canvas id="wave-canvas"></canvas>

                <div class="speech-readout" id="readout">
                    "All systems optimal, sir. Configure your Gemini API key or speak your command."
                </div>

                <div class="input-box">
                    <input type="text" id="cmd-input" placeholder="Speak via Arc Reactor or type your order..." onkeypress="if(event.key==='Enter') sendCommand()">
                    <button class="action-btn" onclick="sendCommand()">EXECUTE</button>
                </div>
            </div>

            <!-- Right: Neural Telemetry Logs -->
            <div class="hud-card">
                <div class="card-title">DIAGNOSTIC LOG FEED</div>
                <div class="log-terminal" id="term-logs">
                    [SYSTEM BOOT] Jinny Core Operating System Online.<br>
                    [MEMORY] Vector SQLite Semantic Store active.<br>
                    [VOICE] Edge Neural TTS ready.<br>
                    [AWAITING] Standing by for instructions...
                </div>
            </div>
        </main>

        <!-- Settings Modal for Gemini Key -->
        <div class="modal-overlay" id="settings-modal">
            <div class="modal-content">
                <h3 style="font-family:'Orbitron',sans-serif; color:var(--cyan); margin-bottom:15px;">CONFIGURE GEMINI AI</h3>
                <p style="font-size:14px; color:#88a0bc; margin-bottom:15px;">Paste your free Google Gemini API Key from Google AI Studio to unlock autonomous thinking and conversation.</p>
                <input type="text" id="key-input" placeholder="AIzaSy..." style="width:100%; margin-bottom:20px;">
                <div style="display:flex; justify-content:flex-end; gap:10px;">
                    <button class="action-btn" style="background:#223344;" onclick="closeModal()">CANCEL</button>
                    <button class="action-btn" onclick="saveApiKey()">ACTIVATE AI</button>
                </div>
            </div>
        </div>

        <audio id="tts-player" autoplay></audio>

        <script>
            const API_KEY = "jinny_live_sec_prod_9948201847192847";
            const readout = document.getElementById("readout");
            const coreText = document.getElementById("core-state");
            const orb = document.getElementById("reactor-orb");
            const logs = document.getElementById("term-logs");
            const player = document.getElementById("tts-player");
            const canvas = document.getElementById("wave-canvas");
            const ctx = canvas.getContext("2d");

            let currentDevices = {};
            let isSpeaking = false;

            function log(msg) {
                const now = new Date().toLocaleTimeString();
                logs.innerHTML += `<br>[${now}] ${msg}`;
                logs.scrollTop = logs.scrollHeight;
            }

            // Waveform animation
            function drawWave() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.beginPath();
                ctx.lineWidth = 2;
                ctx.strokeStyle = isSpeaking ? "#ff3366" : "#00f0ff";
                const mid = canvas.height / 2;
                for (let x = 0; x < canvas.width; x++) {
                    const amp = isSpeaking ? 16 : 4;
                    const y = mid + Math.sin(x * 0.08 + Date.now() * 0.005) * amp;
                    if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }
                ctx.stroke();
                requestAnimationFrame(drawWave);
            }
            drawWave();

            // Speak response via Neural TTS
            async function speakOut(text) {
                isSpeaking = true;
                try {
                    log("Synthesizing neural voice...");
                    const res = await fetch("/api/voice/synthesize", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-Jinny-Api-Key": API_KEY },
                        body: JSON.stringify({ text: text })
                    });
                    if (res.ok) {
                        const blob = await res.blob();
                        player.src = URL.createObjectURL(blob);
                        player.onended = () => { isSpeaking = false; };
                        player.play();
                    } else {
                        const utter = new SpeechSynthesisUtterance(text);
                        utter.pitch = 0.9;
                        utter.onend = () => { isSpeaking = false; };
                        window.speechSynthesis.speak(utter);
                    }
                } catch(e) {
                    isSpeaking = false;
                }
            }

            // Transmit query to Assistant
            async function processQuery(queryText) {
                if(!queryText.trim()) return;
                readout.innerText = `Processing: "${queryText}"...`;
                log(`USER: "${queryText}"`);

                try {
                    const res = await fetch("/api/assistant/interact", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-Jinny-Api-Key": API_KEY },
                        body: JSON.stringify({ query: queryText })
                    });
                    const data = await res.json();
                    const reply = data.speech_output || "Command complete, sir.";
                    readout.innerText = `"${reply}"`;
                    log(`JINNY: ${reply}`);
                    speakOut(reply);
                    fetchDevices();
                } catch(e) {
                    readout.innerText = "Execution failed.";
                    log(`ERROR: ${e.message}`);
                }
            }

            function sendCommand() {
                const input = document.getElementById("cmd-input");
                processQuery(input.value);
                input.value = "";
            }

            // Voice recognition
            let recognition;
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRec();
                recognition.continuous = false;
                recognition.lang = 'en-US';

                recognition.onstart = () => {
                    orb.classList.add("active");
                    coreText.innerHTML = "LISTENING...";
                    log("Voice channel active. Speak your command.");
                };
                recognition.onresult = (e) => {
                    processQuery(e.results[0][0].transcript);
                };
                recognition.onend = () => {
                    orb.classList.remove("active");
                    coreText.innerHTML = "CLICK TO<br>SPEAK";
                };
            }

            function toggleVoiceListening() {
                if (recognition) recognition.start();
                else alert("Microphone supported in Google Chrome.");
            }

            // Interactive IoT Actions
            async function executeDevice(id, action, params = {}) {
                log(`IoT DISPATCH -> ${id} [${action}]`);
                try {
                    await fetch("/api/iot/execute", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-Jinny-Api-Key": API_KEY },
                        body: JSON.stringify({ device_id: id, action: action, params: params })
                    });
                    fetchDevices();
                } catch(e) { log(`IoT Error: ${e.message}`); }
            }

            function toggleDevice(id) {
                const current = currentDevices[id]?.state || "off";
                const next = current === "on" ? "off" : "on";
                executeDevice(id, next);
            }

            function toggleLock() {
                const current = currentDevices["smart_lock"]?.state || "locked";
                const next = current === "locked" ? "unlocked" : "locked";
                executeDevice("smart_lock", next);
            }

            function adjustTemp(delta) {
                let current = currentDevices["ac_unit"]?.temperature || 22;
                current += delta;
                executeDevice("ac_unit", "on", { temperature: current });
            }

            function wakePc() {
                executeDevice("workstation_pc", "wake");
                speakOut("Broadcasting Wake-on-LAN packet to workstation, sir.");
            }

            async function fetchDevices() {
                try {
                    const res = await fetch("/api/iot/devices", {
                        headers: { "X-Jinny-Api-Key": API_KEY }
                    });
                    currentDevices = await res.json();
                    
                    // Update UI state
                    const light = document.getElementById("btn-light");
                    if (currentDevices.living_room_light?.state === "on") {
                        light.className = "toggle-btn on"; light.innerText = "ON";
                    } else {
                        light.className = "toggle-btn off"; light.innerText = "OFF";
                    }

                    const lock = document.getElementById("btn-lock");
                    if (currentDevices.smart_lock?.state === "unlocked") {
                        lock.className = "toggle-btn off"; lock.innerText = "UNLOCKED";
                    } else {
                        lock.className = "toggle-btn on"; lock.innerText = "LOCKED";
                    }

                    document.getElementById("temp-display").innerText = `${currentDevices.ac_unit?.temperature || 22}°C`;
                } catch(e) {}
            }
            setInterval(fetchDevices, 4000);
            fetchDevices();

            // Settings Modal
            function openModal() { document.getElementById("settings-modal").style.display = "flex"; }
            function closeModal() { document.getElementById("settings-modal").style.display = "none"; }

            async function saveApiKey() {
                const key = document.getElementById("key-input").value.trim();
                if (!key) return alert("Please enter an API Key.");
                try {
                    const res = await fetch("/api/settings/gemini-key", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ gemini_api_key: key })
                    });
                    const data = await res.json();
                    log("Gemini AI Core online and activated.");
                    document.getElementById("sys-status").innerText = "● AI CORE ONLINE";
                    document.getElementById("sys-status").style.color = "#00ff88";
                    closeModal();
                    speakOut("AI Core online, sir. All neural inference systems are operational.");
                } catch(e) {
                    alert("Error activating API key: " + e.message);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ----------------- Core API Endpoints -----------------
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
