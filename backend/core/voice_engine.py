"""
Jinny Core - Neural Voice Engine & Audio Synthesis Subsystem
Engineered by Eng. Yousuf Albaz (AI & Systems Engineer)
"""

import logging
import io
import re
from typing import Optional
import edge_tts

logger = logging.getLogger("Jinny.Voice")


class NeuralVoiceEngine:
    def __init__(self):
        # Default English Jarvis Voice (British Male)
        self.en_voice = "en-GB-RyanNeural"
        # Default Arabic Jarvis Voice (Egyptian Male - Natural)
        self.ar_voice = "ar-EG-ShakirNeural"
        
        self.rate = "+0%"
        self.pitch = "-2Hz"

    def _is_arabic(self, text: str) -> bool:
        """Detect if the text contains Arabic characters."""
        if re.search(r'[\u0600-\u06FF]', text):
            return True
        return False

    async def synthesize_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None
    ) -> bytes:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Cannot synthesize empty text.")

        # Auto-detect language and switch voice dynamically
        if voice:
            selected_voice = voice
        else:
            selected_voice = self.ar_voice if self._is_arabic(clean_text) else self.en_voice

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
        return audio_bytes
