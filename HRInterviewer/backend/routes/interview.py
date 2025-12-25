from flask import Blueprint, jsonify, request
from scripts.mic_voice_interview_api import interview_controller, get_session_history
import traceback

interview_bp = Blueprint("interview_bp", __name__)

# ----------- START INTERVIEW -----------
@interview_bp.route("/start", methods=["POST"])
def start_interview():
    try:
        success = interview_controller.start_interview()
        if success:
            return jsonify({
                "status": "started",
                "message": "Interview started. Backend is now recording audio."
            }), 200
        else:
            # Interview is already running
            return jsonify({
                "status": "error", 
                "message": "Interview already running. Call /end first if you want to restart.",
                "is_running": interview_controller.is_running
            }), 400
    except Exception as e:
        print(f"❌ Error in /start endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Failed to start interview: {str(e)}"
        }), 500

# ----------- GET STATUS -----------
@interview_bp.route("/status", methods=["GET"])
def interview_status():
    try:
        status = interview_controller.get_status()
        return jsonify(status), 200
    except Exception as e:
        print(f"❌ Error in /status endpoint: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ----------- END INTERVIEW -----------
@interview_bp.route("/end", methods=["POST"])
def end_interview():
    try:
        interview_controller.end_interview()
        return jsonify({"status": "ended", "message": "Interview ended successfully"}), 200
    except Exception as e:
        print(f"❌ Error in /end endpoint: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ----------- HISTORY -----------
@interview_bp.route("/history", methods=["GET"])
def history():
    try:
        limit = int(request.args.get("limit", 20))
        items = get_session_history(limit=limit)
        return jsonify({"items": items}), 200
    except Exception as e:
        print(f"❌ Error in /history endpoint: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
