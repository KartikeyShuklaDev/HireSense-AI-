# 📌 QUICK REFERENCE CARD

## Backend API Endpoints (Ctrl+C to copy)

### Start Interview
```
POST http://localhost:5000/api/interview/start
Response: 200 {status: "started"} or 400 {status: "error"}
```

### Get Status (Poll every 2 seconds)
```
GET http://localhost:5000/api/interview/status
Response: {is_running: bool, name: string, stage: string, avg_score: float}
```

### End Interview
```
POST http://localhost:5000/api/interview/end
Response: 200 {status: "ended"}
```

### Get History
```
GET http://localhost:5000/api/interview/history?limit=20
Response: {items: [{name, avg_score, timestamp, ...}]}
```

### Check Backend Alive
```
GET http://localhost:5000/
Response: 200 {message: "HR Interview Backend Running"}
```

---

## Commands (Copy & Paste)

### Start Backend
```bash
cd backend && python app.py
```

### Start MongoDB (Windows)
```bash
net start MongoDB
```

### Test Backend
```bash
python test_backend.py
```

### View MongoDB Sessions
```bash
mongo
use HireSense
db.InterviewSessions.find().pretty()
exit()
```

### Clear Terminal Logs
```bash
cls          # Windows
clear        # Mac/Linux
```

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | Good! Continue |
| 400 | Bad request/Already running | Call /end first |
| 500 | Server error | Check backend logs |

---

## Common Issues Quick Fix

### "MongoDB not available"
→ `net start MongoDB`

### "Already running" (400 error)
→ `curl POST /api/interview/end`

### "Backend not running"
→ `python app.py`

### "No history found"
→ `net start MongoDB` (optional)

---

## Log Indicators (In backend terminal)

| Symbol | Meaning | Action |
|--------|---------|--------|
| ✅ | Success | Keep going |
| ⚠️ | Warning | Note it, not critical |
| ❌ | Error | Check TROUBLESHOOTING.md |
| 🔊 | Audio/TTS | Working (shows which one) |
| 📝 | Transcription | Text recognized |
| 🎯 | Score | Question evaluated |
| 🗣️ | Speaking | User input detected |

---

## Configuration Files

### API Constants (Flutter)
**File:** `frontend_app/lib/constants/api_constants.dart`

```dart
static const String baseUrl = "http://192.168.29.186:5000";
```

Change `192.168.29.186` to:
- `localhost` - Same machine
- Your IP - Different machine
- `10.0.2.2` - Android emulator

### Environment Variables
**File:** `backend/.env`

```
ELEVENLAB_API_KEY=...
GEMINI_API_KEY=...
GROQ_API_KEY=...
OPENAI_API_KEY=...
```

---

## File Locations

```
HRInterviewer/
├── backend/
│   ├── app.py              [Start here]
│   ├── routes/interview.py [API endpoints]
│   ├── scripts/mic_voice_interview_api.py [Core logic]
│   └── README.md           [Read this first]
└── frontend_app/
    ├── lib/screens/home_screen.dart
    ├── lib/screens/interview_screen.dart
    ├── lib/screens/history_screen.dart
    └── lib/constants/api_constants.dart [Configure IP here]
```

---

## Key Improvements Applied

1. ✅ **Audio Error Handling** - Can't crash now
2. ✅ **Route Error Handling** - Clear error messages
3. ✅ **Logging** - Full stack traces for debugging
4. ✅ **MongoDB Fallback** - Works without DB
5. ✅ **Backward Compatible** - No breaking changes

---

## Testing in 30 Seconds

```bash
# Terminal 1
cd backend && python app.py

# Terminal 2 (wait 3 seconds)
python test_backend.py

# Should see "✅ Backend test complete!"
```

---

## Deployment Checklist (Final)

- [ ] Backend starts (`python app.py`)
- [ ] Test passes (`python test_backend.py`)
- [ ] MongoDB running (`net start MongoDB`)
- [ ] Flutter can reach backend
- [ ] Interview completes successfully
- [ ] No ❌ errors in logs
- [ ] Ready to deploy!

---

## Emergency Reset

If everything breaks:

```bash
# Stop backend
Ctrl+C in backend terminal

# Stop MongoDB
net stop MongoDB

# Wait 5 seconds

# Start MongoDB
net start MongoDB

# Start backend
python app.py

# Test
python test_backend.py
```

---

## Documentation Files

- 📖 `README.md` - Quick start & API reference
- 🐛 `TROUBLESHOOTING.md` - Fix common issues
- 📋 `IMPROVEMENTS.md` - What was fixed
- 📊 `IMPLEMENTATION_SUMMARY.md` - Technical details
- 📉 `VISUAL_GUIDE.md` - Before/after diagrams
- ✅ `DEPLOYMENT_CHECKLIST.md` - Step-by-step deploy
- 🧪 `test_backend.py` - Automated tests

---

## Ports & URLs

| Service | URL | Port |
|---------|-----|------|
| Backend | http://localhost:5000 | 5000 |
| MongoDB | mongodb://127.0.0.1:27017 | 27017 |
| Flutter | http://device-ip:port | app-dependent |

---

## Support

**For detailed help:**
1. Read appropriate documentation file above
2. Check `TROUBLESHOOTING.md`
3. Look for ❌ symbols in logs
4. Search error message online

**Everything is logged** - check the terminal where backend runs!

---

**Print this card and keep it handy during deployment! 📌**
