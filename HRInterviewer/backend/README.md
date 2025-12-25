# 🚀 Quick Start - Backend API Reference

## Running the Backend

```bash
cd backend
python app.py
```

Expected startup (if MongoDB running):
```
✅ Connected to MongoDB (HireSense.CandidateData).
* Running on http://0.0.0.0:5000
* Press CTRL+C to quit
```

If MongoDB not running:
```
⚠ MongoDB not available: No servers found yet, Timeout: 2.0s...
* Running on http://0.0.0.0:5000
[Interview will still work, history won't be saved]
```

---

## API Endpoints

### 1. Start Interview
```http
POST /api/interview/start
Content-Type: application/json

Response 200:
{
  "status": "started",
  "message": "Interview started. Backend is now recording audio."
}

Response 400 (if already running):
{
  "status": "error",
  "message": "Interview already running. Call /end first if you want to restart.",
  "is_running": true
}
```

### 2. Get Current Status (Poll This Every 2 Seconds)
```http
GET /api/interview/status

Response 200:
{
  "status": "running",
  "is_running": true,
  "name": "John Doe",
  "stage": "TECH",
  "question": "What is a HashMap?",
  "last_score": 75,
  "avg_score": 72.5,
  "completed": false
}
```

### 3. End Interview
```http
POST /api/interview/end

Response 200:
{
  "status": "ended",
  "message": "Interview ended successfully"
}
```

### 4. Get Interview History
```http
GET /api/interview/history?limit=5

Response 200:
{
  "items": [
    {
      "_id": "ObjectId(...)",
      "name": "John Doe",
      "skills": ["Python", "React"],
      "avg_score": 82.5,
      "interactions_count": 8,
      "timestamp": "2024-01-15T10:30:00"
    },
    ...
  ]
}
```

---

## Flutter Frontend Integration

### Set API Base URL
**File:** `frontend_app/lib/constants/api_constants.dart`

```dart
static const String baseUrl = "http://192.168.29.186:5000";
// Change 192.168.29.186 to:
// - "localhost" (if running on same machine)
// - Your LAN IP (if on different machine)
// - "10.0.2.2" (if Android emulator)
```

### Service Usage Example
```dart
import 'package:frontend_app/services/interview_service.dart';

final service = InterviewService();

// Start interview
await service.startInterview();

// Poll status
Timer.periodic(Duration(seconds: 2), (_) async {
  final status = await service.getStatus();
  print("Current score: ${status['avg_score']}");
});

// End interview
await service.endInterview();

// Get history
final history = await service.getHistory(limit: 20);
```

---

## MongoDB Setup

### Windows Installation
1. Download: https://www.mongodb.com/try/download/community
2. Run installer and follow defaults
3. Start service:
   ```cmd
   net start MongoDB
   ```

### Verify Connection
```bash
# Open another terminal
mongo
> db.adminCommand("ping")
{ "ok" : 1 }
> exit()
```

### View Interview Sessions
```bash
mongo
> use HireSense
> db.InterviewSessions.find().pretty()
```

---

## Debugging

### Check if Backend is Running
```bash
curl http://localhost:5000/
# Should return: {"message": "HR Interview Backend Running"}
```

### Check Interview Status
```bash
curl http://localhost:5000/api/interview/status
```

### View Backend Logs
The terminal where you ran `python app.py` will show all logs:
- 🎤 Audio input events
- 🔊 Audio output events
- 📝 Transcription results
- 🎯 Scoring results
- ❌ Any errors or warnings

### Common Issues

| Issue | Solution |
|-------|----------|
| **Connection refused** | Backend not running - `python app.py` |
| **400 error on 2nd start** | Interview still running - call `/end` first |
| **No audio playing** | Check TTS API keys in code |
| **"No servers found"** | MongoDB not running - `net start MongoDB` |
| **CORS error in Flutter** | Already handled, shouldn't happen |
| **Empty history** | MongoDB not running (it's OK, just won't persist) |

---

## Interview Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. GET Candidate Name (Voice Input)                     │
│    → record_from_mic() → stt_transcribe()               │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 2. HR Round (3 questions answered)                       │
│    Stage: "HR" | Status: running                        │
│    → tts_say() → record_from_mic() → stt_transcribe()  │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 3. Technical Round (3 questions + scoring)              │
│    Stage: "TECH" | Score: updated in real-time          │
│    → question from RAG → evaluate_answer()              │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 4. Final Q&A                                            │
│    Stage: "TECH" | Completed: true                      │
│    → Candidate can ask questions                        │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 5. Save to MongoDB                                      │
│    - Candidate name & skills                            │
│    - All interactions                                    │
│    - Final avg_score                                    │
└─────────────────────────────────────────────────────────┘

Frontend polls /status every 2 seconds and updates UI.
```

---

## Performance Tips

1. **MongoDB Indexing** (if available):
   ```bash
   mongo
   > use HireSense
   > db.InterviewSessions.createIndex({name: 1})
   > db.InterviewSessions.createIndex({timestamp: -1})
   ```

2. **Logs are verbose** - Set `debug=False` in production:
   ```python
   # app.py
   app.run(host="0.0.0.0", port=5000, debug=False)
   ```

3. **API Keys** - Store in environment variables:
   ```bash
   # .env (create this file)
   ELEVENLAB_API_KEY=...
   GEMINI_API_KEY=...
   GROQ_API_KEY=...
   OPENAI_API_KEY=...
   ```

---

## Deployment Checklist

- [ ] MongoDB running and accepting connections
- [ ] API keys set in environment variables
- [ ] Backend starts without errors
- [ ] Flutter app configured with correct backend URL
- [ ] Test `/start` → `/status` → `/end` flow
- [ ] Test `/history` endpoint has previous interviews
- [ ] Verify audio playback works (or at least doesn't crash)
- [ ] Check phone/emulator can reach backend IP:5000

---

**Need help?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
