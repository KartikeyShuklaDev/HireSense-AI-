from flask import Flask
from flask_cors import CORS
from routes.interview import interview_bp


def create_app():
    app = Flask(__name__)

    # Allow Flutter app (Edge/emulator/device) to call the backend
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register all API routes (frontend expects /api/interview/*)
    app.register_blueprint(interview_bp, url_prefix="/api/interview")

    @app.get("/")
    def home():
        return {"message": "HR Interview Backend Running"}, 200

    @app.get("/api/interview/ping")
    def ping():
        return {"status": "ok"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
