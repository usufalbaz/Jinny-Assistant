"""
Jinny Core - Production FastAPI Server & Ultimate Sci-Fi HUD
Architected & Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s : %(message)s")
logger = logging.getLogger("Jinny.Server")

memory_store = PersistentMemoryStore()
sms_dispatcher = SmsDispatcher()
iot_controller = IoTController()
voice_engine = NeuralVoiceEngine()
assistant_core = JinnyAssistantCore(memory_store, sms_dispatcher, iot_controller)
proactive_agent = ProactiveAutonomousAgent(memory_store, iot_controller, sms_dispatcher)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await memory_store.initialize()
    await proactive_agent.start()
    yield
    await proactive_agent.stop()

app = FastAPI(title="Jinny Core AI Gateway", version=settings.VERSION, lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)

async def verify_api_key(api_key: Optional[str] = Security(api_key_header)):
    if settings.DEBUG: return True
    if not api_key or api_key != settings.JINNY_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

class QueryRequest(BaseModel):
    query: str
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
    gemini_model: str

@app.post("/api/settings/gemini-key")
async def update_gemini_api_key(req: ApiKeyUpdateRequest):
    settings.GEMINI_API_KEY = req.gemini_api_key.strip()
    settings.GEMINI_MODEL = req.gemini_model.strip()
    assistant_core.client = genai.Client(api_key=settings.GEMINI_API_KEY)
    memory_store.client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return {"status": "success"}

# ----------------- THE ULTIMATE JARVIS HUD -----------------
@app.get("/", response_class=HTMLResponse)
async def jarvis_holographic_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>JINNY // STARK OS</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&family=Cairo:wght@400;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --cyan: #00e5ff;
                --cyan-glow: rgba(0, 229, 255, 0.5);
                --dark-bg: #050914;
                --panel-bg: rgba(10, 18, 35, 0.75);
                --red: #ff2a5f;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; user-select: none; }
            body {
                background-color: var(--dark-bg);
                color: #e2f1ff;
                font-family: 'Rajdhani', 'Cairo', sans-serif;
                height: 100vh;
                width: 100vw;
                overflow: hidden; /* Prevent ANY scrolling on the page */
                display: flex;
                flex-direction: column;
            }
            #canvas-bg { position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1; pointer-events: none; opacity: 0.6; }
            body::after {
                content: " "; display: block; position: absolute; top: 0; left: 0; bottom: 0; right: 0;
                background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
                z-index: 2; background-size: 100% 3px; pointer-events: none;
            }
            header, main, .modal-overlay { z-index: 10; position: relative; }
            header {
                padding: 15px 40px; display: flex; justify-content: space-between; align-items: center;
                border-bottom: 1px solid rgba(0, 229, 255, 0.3);
                background: linear-gradient(90deg, rgba(0,229,255,0.05) 0%, transparent 50%, rgba(0,229,255,0.05) 100%);
            }
            .logo { font-family: 'Orbitron', sans-serif; font-size: 26px; font-weight: 900; letter-spacing: 4px; color: var(--cyan); text-shadow: 0 0 15px var(--cyan-glow); }
            .header-controls { display: flex; gap: 15px; align-items: center; }
            .mic-lang-btn {
                background: rgba(0, 229, 255, 0.05); border: 1px solid var(--cyan); color: var(--cyan);
                padding: 6px 18px; border-radius: 4px; cursor: pointer; font-family: 'Orbitron', sans-serif; font-weight: bold; transition: 0.3s;
            }
            .mic-lang-btn:hover { background: var(--cyan); color: #000; box-shadow: 0 0 15px var(--cyan-glow); }
            main { flex: 1; display: grid; grid-template-columns: 350px 1fr 350px; gap: 30px; padding: 30px; height: calc(100vh - 70px); overflow: hidden; }
            .hud-card {
                background: var(--panel-bg); border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 16px; padding: 25px;
                backdrop-filter: blur(10px); box-shadow: 0 0 30px rgba(0,0,0,0.5); display: flex; flex-direction: column; position: relative;
                overflow: hidden;
            }
            .card-title { font-family: 'Orbitron', sans-serif; font-size: 14px; letter-spacing: 3px; color: var(--cyan); margin-bottom: 20px; border-bottom: 1px dashed rgba(0, 229, 255, 0.3); padding-bottom: 10px; }
            .device-row { display: flex; justify-content: space-between; align-items: center; padding: 15px; margin-bottom: 12px; background: rgba(0, 229, 255, 0.03); border: 1px solid rgba(0, 229, 255, 0.1); border-radius: 8px; transition: 0.3s; }
            .toggle-btn { padding: 6px 18px; font-family: 'Orbitron', sans-serif; font-weight: bold; border-radius: 4px; cursor: pointer; border: 1px solid; transition: 0.3s; }
            .toggle-btn.on { background: var(--cyan); color: #000; border-color: var(--cyan); box-shadow: 0 0 15px var(--cyan-glow); }
            .toggle-btn.off { background: transparent; color: #557; border-color: #335; }
            .toggle-btn:disabled { opacity: 0.5; cursor: not-allowed; }
            
            .center-stage { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; }
            .reactor-container { position: relative; width: 260px; height: 260px; display: flex; justify-content: center; align-items: center; cursor: pointer; }
            .ring { position: absolute; border-radius: 50%; border: 2px solid transparent; }
            .ring-1 { width: 260px; height: 260px; border-top: 2px solid var(--cyan); border-bottom: 2px solid var(--cyan); animation: spin 8s linear infinite; }
            .ring-2 { width: 230px; height: 230px; border-left: 2px dashed var(--cyan); border-right: 2px dashed var(--cyan); animation: spin-reverse 12s linear infinite; }
            .ring-3 { width: 200px; height: 200px; border: 3px solid rgba(0, 229, 255, 0.2); box-shadow: 0 0 40px var(--cyan-glow) inset; }
            .core-btn {
                width: 140px; height: 140px; background: rgba(0, 229, 255, 0.1); border-radius: 50%; display: flex; justify-content: center; align-items: center;
                font-family: 'Orbitron', sans-serif; font-size: 14px; font-weight: 900; letter-spacing: 2px; color: #fff; text-shadow: 0 0 10px var(--cyan); box-shadow: 0 0 50px var(--cyan-glow);
                transition: 0.3s; z-index: 5; text-align: center; line-height: 1.5;
            }
            .reactor-container:hover .core-btn { transform: scale(1.1); background: rgba(0, 229, 255, 0.2); }
            .reactor-container.listening .ring-1 { border-color: var(--red); animation: spin 2s linear infinite; }
            .reactor-container.listening .ring-2 { border-color: var(--red); }
            .reactor-container.listening .core-btn { box-shadow: 0 0 80px rgba(255,0,60,0.8); text-shadow: 0 0 10px var(--red); }

            /* FIX: Strictly Fixed Height Text Box */
            .text-container { 
                margin-top: 40px; 
                width: 90%; 
                max-width: 650px; 
                height: 140px !important; 
                min-height: 140px; 
                background: rgba(0,0,0,0.4); 
                border: 1px solid rgba(0,229,255,0.2); 
                border-radius: 8px; 
                padding: 15px; 
                overflow-y: auto; 
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .text-container::-webkit-scrollbar { width: 4px; }
            .text-container::-webkit-scrollbar-thumb { background: var(--cyan); border-radius: 2px; }
            .speech-readout { font-size: 18px; color: #fff; line-height: 1.6; text-shadow: 0 0 8px rgba(0, 229, 255, 0.5); text-align: center; margin: 0; }
            
            .input-box { margin-top: 20px; width: 90%; display: flex; gap: 10px; }
            input[type="text"] { flex: 1; background: rgba(0, 0, 0, 0.6); border: 1px solid var(--cyan); border-radius: 6px; padding: 15px; color: #fff; font-size: 16px; font-family: 'Cairo', sans-serif; outline: none; }
            input[type="text"]:focus { box-shadow: 0 0 15px var(--cyan-glow); }
            .log-terminal { font-family: monospace; font-size: 13px; color: #6a9fb5; overflow-y: auto; flex: 1; line-height: 1.7; }
            
            /* FIX: Modal closes when clicking outside */
            .modal-overlay { display: none; position: fixed; top:0; left:0; width:100vw; height:100vh; background: rgba(0,0,0,0.85); justify-content: center; align-items: center; cursor: pointer; }
            .modal-content { background: #020610; border: 2px solid var(--cyan); box-shadow: 0 0 50px var(--cyan-glow); padding: 30px; width: 400px; border-radius: 12px; cursor: default; }
            
            @keyframes spin { 100% { transform: rotate(360deg); } }
            @keyframes spin-reverse { 100% { transform: rotate(-360deg); } }
        </style>
    </head>
    <body>
        <canvas id="canvas-bg"></canvas>

        <header>
            <div class="logo">⚡ JINNY // OS</div>
            <div class="header-controls">
                <button class="mic-lang-btn" id="lang-btn" onclick="toggleLang()">MIC: ARABIC</button>
                <button class="mic-lang-btn" onclick="openModal()">⚙️ AI SETUP</button>
            </div>
        </header>

        <main>
            <div class="hud-card">
                <div class="card-title">HARDWARE LINK</div>
                <div class="device-row">
                    <div><div style="font-weight:bold">Living Room Light</div><small style="color:#6e859d">Main Relay</small></div>
                    <button class="toggle-btn off" id="btn-light" onclick="toggleDevice('living_room_light', this)">OFF</button>
                </div>
                <div class="device-row">
                    <div><div style="font-weight:bold">Smart Lock</div><small style="color:#6e859d">Front Door</small></div>
                    <button class="toggle-btn on" id="btn-lock" onclick="toggleLock(this)">LOCKED</button>
                </div>
                <div class="device-row">
                    <div><div style="font-weight:bold">Workstation PC</div><small style="color:#6e859d">Wake-on-LAN</small></div>
                    <button class="toggle-btn off" onclick="executeDevice('workstation_pc', 'wake', this)">WAKE</button>
                </div>
            </div>

            <div class="center-stage">
                <div class="reactor-container" id="reactor" onclick="startMic()">
                    <div class="ring ring-1"></div>
                    <div class="ring ring-2"></div>
                    <div class="ring ring-3"></div>
                    <div class="core-btn" id="core-text">INITIATE<br>VOICE</div>
                </div>
                <div class="text-container">
                    <p class="speech-readout" id="readout">"Systems online, sir. Waiting for your command."</p>
                </div>
                <div class="input-box">
                    <input type="text" id="cmd-input" placeholder="Type command here..." onkeypress="if(event.key==='Enter') sendCommand()">
                    <button class="mic-lang-btn" onclick="sendCommand()">SEND</button>
                </div>
            </div>

            <div class="hud-card">
                <div class="card-title">SYSTEM LOGS</div>
                <div class="log-terminal" id="term-logs">
                    [BOOT] Holographic UI Initialized.<br>
                    [VOICE] English/Arabic dynamic TTS ready.<br>
                </div>
            </div>
        </main>

        <!-- FIX: Modal onclick closes it -->
        <div class="modal-overlay" id="settings-modal" onclick="if(event.target === this) closeModal()">
            <div class="modal-content">
                <h3 style="color:var(--cyan); font-family:'Orbitron'; margin-bottom:20px;">SYSTEM CONFIG</h3>
                <input type="text" id="key-input" placeholder="Gemini API Key..." style="width:100%; margin-bottom:15px;">
                <input type="text" id="model-input" value="gemini-1.5-flash" placeholder="Model Name (e.g. gemini-1.5-flash)" style="width:100%; margin-bottom:25px;">
                <div style="display:flex; justify-content:flex-end; gap:10px;">
                    <button class="mic-lang-btn" style="background:transparent;" onclick="closeModal()">CLOSE</button>
                    <button class="mic-lang-btn" onclick="saveApiKey()">SAVE</button>
                </div>
            </div>
        </div>

        <audio id="tts-player" autoplay></audio>

        <script>
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            function playBeep(freq, type, duration, vol=0.1) {
                if(audioCtx.state === 'suspended') audioCtx.resume();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = type; osc.frequency.value = freq;
                osc.connect(gain); gain.connect(audioCtx.destination);
                gain.gain.setValueAtTime(vol, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
                osc.start(); osc.stop(audioCtx.currentTime + duration);
            }
            document.querySelectorAll('button').forEach(b => b.addEventListener('click', () => playBeep(800, 'sine', 0.1)));

            const canvas = document.getElementById('canvas-bg');
            const ctx = canvas.getContext('2d');
            canvas.width = window.innerWidth; canvas.height = window.innerHeight;
            const particles = [];
            for(let i=0; i<80; i++) particles.push({x: Math.random()*canvas.width, y: Math.random()*canvas.height, vx: (Math.random()-0.5)*0.5, vy: (Math.random()-0.5)*0.5});
            function drawParticles() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = 'rgba(0, 229, 255, 0.5)';
                ctx.strokeStyle = 'rgba(0, 229, 255, 0.1)';
                particles.forEach(p => {
                    p.x += p.vx; p.y += p.vy;
                    if(p.x < 0 || p.x > canvas.width) p.vx *= -1;
                    if(p.y < 0 || p.y > canvas.height) p.vy *= -1;
                    ctx.beginPath(); ctx.arc(p.x, p.y, 1.5, 0, Math.PI*2); ctx.fill();
                    particles.forEach(p2 => {
                        const dist = Math.hypot(p.x-p2.x, p.y-p2.y);
                        if(dist < 100) { ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p2.x, p2.y); ctx.stroke(); }
                    });
                });
                requestAnimationFrame(drawParticles);
            }
            drawParticles();

            const API_KEY = "jinny_live_sec_prod_9948201847192847";
            let micLang = 'ar-EG';
            const readout = document.getElementById("readout");
            const logs = document.getElementById("term-logs");
            const player = document.getElementById("tts-player");
            const reactor = document.getElementById("reactor");
            const coreText = document.getElementById("core-text");

            function log(msg) {
                const now = new Date().toLocaleTimeString();
                logs.innerHTML += `<br>[${now}] ${msg}`;
                logs.scrollTop = logs.scrollHeight;
            }

            function toggleLang() {
                const btn = document.getElementById("lang-btn");
                if(micLang === 'ar-EG') { micLang = 'en-US'; btn.innerText = "MIC: ENGLISH"; }
                else { micLang = 'ar-EG'; btn.innerText = "MIC: ARABIC"; }
                playBeep(1200, 'square', 0.1);
                log(`Microphone language switched to ${micLang}`);
            }

            async function speakOut(text) {
                try {
                    log("Synthesizing voice...");
                    const res = await fetch("/api/voice/synthesize", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-Jinny-Api-Key": API_KEY },
                        body: JSON.stringify({ text: text })
                    });
                    if (res.ok) {
                        const blob = await res.blob();
                        player.src = URL.createObjectURL(blob);
                        player.play();
                    }
                } catch(e) { log("Voice Error: " + e.message); }
            }

            async function processQuery(queryText) {
                if(!queryText.trim()) return;
                readout.innerText = `Processing: "${queryText}"...`;
                log(`USER: ${queryText}`);
                playBeep(400, 'sawtooth', 0.2);
                
                try {
                    const res = await fetch("/api/assistant/interact", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-Jinny-Api-Key": API_KEY },
                        body: JSON.stringify({ query: queryText })
                    });
                    const data = await res.json();
                    const reply = data.speech_output || "Done.";
                    readout.innerText = reply;
                    log(`JINNY: ${reply}`);
                    speakOut(reply);
                    fetchDevices();
                } catch(e) {
                    readout.innerText = "Connection failed.";
                    log(`ERROR: ${e.message}`);
                }
            }

            function sendCommand() {
                const input = document.getElementById("cmd-input");
                processQuery(input.value);
                input.value = "";
            }

            let recognition;
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRec();
                recognition.continuous = false;
            }

            function startMic() {
                if (!recognition) return alert("Mic not supported in this browser.");
                playBeep(900, 'sine', 0.2);
                recognition.lang = micLang;
                recognition.onstart = () => { reactor.classList.add("listening"); coreText.innerHTML = "LISTENING"; };
                recognition.onresult = (e) => { processQuery(e.results[0][0].transcript); };
                recognition.onend = () => { reactor.classList.remove("listening"); coreText.innerHTML = "INITIATE<br>VOICE"; };
                try { recognition.start(); } catch(e) { log("Mic error: " + e.message); }
            }

            async function executeDevice(id, action, btnElement = null) {
                if(btnElement) { btnElement.disabled = true; btnElement.innerText = "..."; }
                try {
                    await fetch("/api/iot/execute", {
                        method: "POST",
                        headers: { "Content-Type": "application/json", "X-Jinny-Api-Key": API_KEY },
                        body: JSON.stringify({ device_id: id, action: action })
                    });
                    fetchDevices();
                } catch(e) { log(`IoT Error: ${e.message}`); }
                if(btnElement) btnElement.disabled = false;
            }

            let currentDevices = {};
            function toggleDevice(id, btn) {
                const action = currentDevices[id]?.state === "on" ? "off" : "on";
                executeDevice(id, action, btn);
            }
            function toggleLock(btn) {
                const action = currentDevices["smart_lock"]?.state === "locked" ? "unlocked" : "locked";
                executeDevice("smart_lock", action, btn);
            }

            async function fetchDevices() {
                try {
                    const res = await fetch("/api/iot/devices", { headers: { "X-Jinny-Api-Key": API_KEY } });
                    currentDevices = await res.json();
                    const light = document.getElementById("btn-light");
                    if (currentDevices.living_room_light?.state === "on") { light.className = "toggle-btn on"; light.innerText = "ON"; } 
                    else { light.className = "toggle-btn off"; light.innerText = "OFF"; }
                    const lock = document.getElementById("btn-lock");
                    if (currentDevices.smart_lock?.state === "unlocked") { lock.className = "toggle-btn off"; lock.innerText = "UNLOCKED"; } 
                    else { lock.className = "toggle-btn on"; lock.innerText = "LOCKED"; }
                } catch(e) {}
            }
            setInterval(fetchDevices, 3000); fetchDevices();

            function openModal() { document.getElementById("settings-modal").style.display = "flex"; playBeep(600, 'sine', 0.1); }
            function closeModal() { document.getElementById("settings-modal").style.display = "none"; playBeep(400, 'sine', 0.1); }
            
            async function saveApiKey() {
                const key = document.getElementById("key-input").value.trim();
                const model = document.getElementById("model-input").value.trim();
                if (!key || !model) return alert("Required fields missing.");
                try {
                    await fetch("/api/settings/gemini-key", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ gemini_api_key: key, gemini_model: model })
                    });
                    log(`AI Core online with model: ${model}`);
                    closeModal();
                    speakOut("Systems updated. I am ready, sir.");
                } catch(e) { alert("Error: " + e.message); }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "system": "Jinny Core",
        "version": settings.VERSION,
        "author": "Eng. Yousuf Albaz"
    }

@app.post("/api/assistant/interact", dependencies=[Depends(verify_api_key)])
async def interact_with_assistant(req: QueryRequest):
    return await assistant_core.process_user_intent(req.query, req.metadata)

@app.post("/api/voice/synthesize", dependencies=[Depends(verify_api_key)])
async def synthesize_voice(req: VoiceSynthesizeRequest):
    audio_bytes = await voice_engine.synthesize_speech(req.text, req.voice)
    return Response(content=audio_bytes, media_type="audio/mpeg")

@app.get("/api/iot/devices", dependencies=[Depends(verify_api_key)])
async def list_iot_devices(): return iot_controller.list_devices()

@app.post("/api/iot/execute", dependencies=[Depends(verify_api_key)])
async def execute_iot_command(req: IoTCommandRequest):
    return await iot_controller.execute_device_command(req.device_id, req.action, req.params)

@app.post("/api/proactive/trigger", dependencies=[Depends(verify_api_key)])
async def trigger_proactive_briefing():
    briefing = await proactive_agent.generate_system_briefing()
    await proactive_agent._broadcast_voice_briefing(briefing)
    return {"status": "broadcasted", "briefing": briefing}

@app.websocket("/ws/android-bridge")
async def android_telemetry_bridge(
    websocket: WebSocket,
    client_id: str = Query("android_primary"),
    token: Optional[str] = Query(None)
):
    if not settings.DEBUG and token != settings.JINNY_API_KEY:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await websocket.accept()
    sms_dispatcher.register_android_client(client_id, websocket)
    await sms_dispatcher.flush_queued_tasks_for_client(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("type")
            if command == "HEARTBEAT":
                await websocket.send_json({"type": "PONG", "timestamp": data.get("timestamp")})
            elif command == "VOICE_STREAM_INPUT":
                text = data.get("text", "")
                res = await assistant_core.process_user_intent(text)
                await websocket.send_json({"type": "ASSISTANT_REPLY", "data": res})
            elif command == "SMS_DELIVERY_REPORT":
                sms_dispatcher.record_delivery_report(data.get("task_id"), data.get("status"), data.get("error"))
    except WebSocketDisconnect:
        sms_dispatcher.unregister_android_client(client_id)
