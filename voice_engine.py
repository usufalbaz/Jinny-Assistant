"""
Jinny Core - Neural Voice Engine & Audio Synthesis Subsystem
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)

Features:
- High-fidelity neural voice synthesis using Microsoft Edge TTS protocol.
- Jarvis-tuned pitch, rate, and timbre (default: en-GB-RyanNeural).
- Asynchronous in-memory audio streaming (MP3 output).
"""

import logging
import io
from typing import Optional
import edge_tts

logger = logging.getLogger("Jinny.Voice")


class NeuralVoiceEngine:
    """
    Synthesizes conversational text into human-grade neural voice streams.
    """

    def __init__(
        self,
        default_voice: str = "en-GB-RyanNeural",
        default_rate: str = "+0%",
        default_pitch: str = "-2Hz"
    ):
        self.voice = default_voice
        self.rate = default_rate
        self.pitch = default_pitch

    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None
    ) -> bytes:
        """
        Synthesize text into raw MP3 audio bytes asynchronously.
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Cannot synthesize empty text.")

        selected_voice = voice or self.voice
        selected_rate = rate or self.rate
        selected_pitch = pitch or self.pitch

        logger.info(f"Synthesizing voice output via [{selected_voice}]: '{clean_text[:40]}...'")

        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=selected_voice,
            rate=selected_rate,
            pitch=selected_pitch
        )

        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        audio_bytes = audio_buffer.getvalue()
        logger.info(f"Generated neural audio payload: {len(audio_bytes)} bytes.")
        return audio_bytes
