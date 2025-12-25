# backend/services/elevenlabs_service.py

import os
from io import BytesIO

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

load_dotenv()

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVEN_API_KEY:
    print("⚠ ELEVENLABS_API_KEY not set. ElevenLabs TTS/STT will be disabled.")
    eleven_client = None
else:
    eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY)


def eleven_tts(text: str) -> bool:
    """
    ElevenLabs Text-To-Speech.
    Plays audio directly to speakers via elevenlabs.play().
    Returns True if audio played, False otherwise.
    """
    if not text or not text.strip():
        return False

    if eleven_client is None:
        print("⚠ ElevenLabs client not initialized (no API key).")
        return False

    try:
        # We don't care about 'output_format' externally – just pick one that works.
        audio = eleven_client.text_to_speech.convert(
            text=text,
            voice_id="VG7gYikNQ71LJ52W9fAD",  # <- your voice ID
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        print("🔊 ElevenLabs TTS used.")
        play(audio)  # streams straight to speakers
        return True
    except Exception as e:
        print(f"❌ ElevenLabs TTS error: {e}")
        return False


def eleven_stt(wav_bytes: bytes) -> str:
    """
    ElevenLabs Speech-To-Text (Scribe).
    Takes WAV bytes, returns transcription text (or "" on failure).
    """
    if eleven_client is None:
        print("⚠ ElevenLabs client not initialized (no API key).")
        return ""

    try:
        # ElevenLabs expects a file-like object
        audio_data = BytesIO(wav_bytes)

        transcription = eleven_client.speech_to_text.convert(
            file=audio_data,
            model_id="scribe_v1",
            tag_audio_events=False,
            diarize=False,
            language_code="eng",  # English
        )

        if hasattr(transcription, "text"):
            text = transcription.text
        elif isinstance(transcription, dict) and "text" in transcription:
            text = transcription["text"]
        else:
            text = str(transcription)

        text = (text or "").strip()
        if text:
            print("🔊 ElevenLabs STT used.")
        return text

    except Exception as e:
        print(f"❌ ElevenLabs STT error: {e}")
        return ""
