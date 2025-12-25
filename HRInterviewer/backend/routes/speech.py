from flask import Blueprint, request, jsonify, send_file
from services.speech_service import (
    tts_multi_speaker,
    transcribe_audio_bytes,
)

speech_bp = Blueprint("speech", __name__)


@speech_bp.route("/tts-multi", methods=["POST"])
def tts_multi():
    """
    Multi-speaker TTS for Interviewer/Candidate style script.

    JSON body:
    {
      "script": "Interviewer: ...\\nCandidate: ...",
      "file_name": "optional.wav"   # optional
    }

    Returns:
    {
      "audio_file": "absolute/path/to/file.wav"
    }
    """
    data = request.get_json(silent=True) or {}
    script = data.get("script")
    file_name = data.get("file_name")

    if not script:
        return jsonify({"error": "script is required"}), 400

    try:
        path = tts_multi_speaker(script=script, file_name=file_name)
        return jsonify({"audio_file": path}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@speech_bp.route("/stt", methods=["POST"])
def stt():
    """
    Speech-to-Text endpoint.

    Expects multipart/form-data:
      audio: <file>

    Returns detailed transcription:
    {
      "summary": "...",
      "segments": [
        {
          "speaker": "...",
          "timestamp": "MM:SS",
          "content": "...",
          "language": "...",
          "language_code": "...",
          "translation": "...",
          "emotion": "happy|sad|angry|neutral"
        },
        ...
      ]
    }
    """
    if "audio" not in request.files:
        return jsonify({"error": "audio file is required (field name 'audio')"}), 400

    audio_file = request.files["audio"]
    audio_bytes = audio_file.read()
    mime_type = audio_file.mimetype or "audio/wav"

    try:
        result = transcribe_audio_bytes(audio_bytes, mime_type=mime_type)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
