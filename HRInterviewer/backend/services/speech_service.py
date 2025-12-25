# backend/services/speech_service.py

import uuid
import wave
from pathlib import Path

from google.genai import types as ga_types

# Reuse the same Gemini client from gemini_service.py
from services.gemini_service import client

# Audio output directory: backend/data/audio
AUDIO_DIR = Path(__file__).resolve().parent.parent / "data" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def _write_wave_file(
    filename: Path,
    pcm: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2,
) -> None:
    """
    Save raw PCM bytes as a .wav file so it can be played by any audio player.
    """
    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


# ─────────────────────────────────────────
#  TEXT → SPEECH  (INTERVIEWER SPEAKS)
# ─────────────────────────────────────────

def tts_interviewer(text: str, file_name: str | None = None) -> str:
    """
    Convert interviewer text into spoken audio using Gemini TTS.

    Args:
        text: The question/sentence that the interviewer will speak.
        file_name: Optional custom WAV file name. If None, a random name is used.

    Returns:
        Absolute path to the generated .wav file.
    """
    if not text or not text.strip():
        raise ValueError("text cannot be empty for TTS")

    if file_name is None:
        file_name = f"interviewer_{uuid.uuid4().hex}.wav"

    out_path = AUDIO_DIR / file_name

    # ✅ Correct TTS model name from official docs:
    # model="gemini-2.5-flash-preview-tts"
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=ga_types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=ga_types.SpeechConfig(
                voice_config=ga_types.VoiceConfig(
                    prebuilt_voice_config=ga_types.PrebuiltVoiceConfig(
                        voice_name="Kore"  # neutral, firm voice
                    )
                )
            ),
        ),
    )

    # Audio bytes come as PCM in inline_data.data
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    _write_wave_file(out_path, audio_data)

    return str(out_path)


# ─────────────────────────────────────────
#  SPEECH → TEXT  (USER ANSWERS)
# ─────────────────────────────────────────

def transcribe_audio_bytes(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """
    Convert user's spoken answer (audio bytes) into plain text using Gemini.

    Args:
        audio_bytes: Raw bytes of the audio file (WAV/MP3/etc.).
        mime_type: MIME type of the audio ("audio/wav", "audio/mpeg", ...).

    Returns:
        Transcript string (plain text).
    """
    if not audio_bytes:
        raise ValueError("audio_bytes is empty")

    prompt = (
        "Transcribe this audio into plain text. "
        "Output only the transcription, no extra explanation."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",  # text model, good for STT post-processing
        contents=[
            ga_types.Content(
                parts=[
                    ga_types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type=mime_type,
                    ),
                    ga_types.Part(text=prompt),
                ]
            )
        ],
        config=ga_types.GenerateContentConfig(
            max_output_tokens=1024,
        ),
    )

    transcript = (response.text or "").strip()
    return transcript
