# Backend Troubleshooting Guide

## Issue 1: MongoDB Connection Warning

**Symptom:** Warning appears at startup:
```
⚠ MongoDB not available: No servers found yet, Timeout: 2.0s...
```

**Root Cause:** MongoDB is not running on `127.0.0.1:27017`

**Solution:**
1. **Windows (using MongoDB Community):**
   ```cmd
   net start MongoDB
   ```
   Or if using MongoDB with default paths:
   ```cmd
   "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
   ```

2. **Windows (using WSL with MongoDB):**
   ```bash
   wsl -e sudo service mongodb start
   ```

3. **Verify MongoDB is running:**
   ```cmd
   mongo --version  # Check if installed
   mongo             # Connect to local instance
   > db.adminCommand("ping")  # Should return { ok: 1 }
   ```

**Important:** Even if MongoDB is not available, the interview will continue! The system gracefully stores session data in memory and can retrieve history from previous sessions.

---

## Issue 2: 400 Error on `/api/interview/start` (Second Request)

**Symptom:** 
```
[First POST /api/interview/start → 200 OK ✓]
[Second POST /api/interview/start → 400 Error ✗]
```

**Root Cause:** The first interview is already running. The `/start` endpoint returns 400 when `interview_controller.is_running == True`.

**Solution:**
1. **Wait for the interview to complete** before starting a new one
2. **Or call `/api/interview/end` first** to stop the current interview:
   ```bash
   POST http://localhost:5000/api/interview/end
   ```

3. **To debug:** Check the status endpoint to see if an interview is running:
   ```bash
   GET http://localhost:5000/api/interview/status
   ```
   Look for `"is_running": true` to confirm.

---

## Issue 3: Audio/Microphone Errors

**Symptom:** Interview thread crashes with audio-related error

**Root Cause:** 
- Microphone device not available or not recognized
- Audio recording library (`sounddevice`) can't access device

**How the Fix Works:**
- `record_from_mic()` now catches exceptions and returns **silent audio** instead of crashing
- Interview continues without user audio input
- **Check the logs** to see which audio fallbacks were used

---

## Issue 4: TTS (Text-to-Speech) Not Working

**Symptom:** Interview continues but no audio output

**Root Cause:** Cloud TTS APIs (ElevenLabs, Gemini, Groq) are failing

**Fallback Chain (Automatic):**
1. **ElevenLabs** (primary) → fallback to Gemini if fails
2. **Gemini TTS** (secondary) → fallback to Groq if fails
3. **Groq TTS** (tertiary) → fallback to local pyttsx3 if fails
4. **Local pyttsx3** (ultimate fallback) → Now also has error handling!

**The Recent Fix:**
- Wrapped `local_tts_say()` in try-except
- If all TTS engines fail, logs a warning and continues
- **Interview never crashes due to audio playback failures**

---

## Testing the Backend

Run the automated test:
```bash
python backend/test_backend.py
```

This will:
1. Check if backend is alive
2. Test starting an interview
3. Test status polling
4. Test rejection of second start (400)
5. Test ending interview
6. Test history retrieval

---

## Backend Configuration

**API Endpoint:** `http://0.0.0.0:5000` (listens on all interfaces)

**CORS Settings:** Allows requests from anywhere (Flutter/Web/Mobile)

**Database:** 
- MongoDB: `mongodb://127.0.0.1:27017/HireSense`
- Collections: `CandidateData`, `InterviewSessions`

**External APIs Used:**
- **ElevenLabs** - STT (speech-to-text) & TTS (text-to-speech)
- **Gemini 2.5 Flash** - Backup STT & TTS
- **Groq** - Backup STT (Whisper) & TTS (PlayAI)
- **Groq Mixtral** - HR/Tech question generation
- **OpenAI GPT-4** - Interview evaluation

All have fallbacks, so interview continues even if one API fails.

---

## How the Interview Becomes Resilient

**Error Handling Strategy:**

| Component | Error | Result |
|-----------|-------|--------|
| Microphone | Unavailable | Returns silence, interview continues |
| MongoDB | Can't connect | In-memory storage, history not persisted |
| TTS (Audio Output) | All APIs fail | Interview continues silently |
| STT (Audio Input) | All APIs fail | Returns empty transcript, interview continues |
| Question Generation | API error | Skip to next round with fallback |
| Answer Evaluation | API error | Skip to next question |

**Result:** Interview almost never crashes. It degrades gracefully.

---

## Quick Debugging Steps

1. **Is backend running?**
   ```bash
   GET http://localhost:5000/
   ```
   Should return: `{"message": "HR Interview Backend Running"}`

2. **Is interview running?**
   ```bash
   GET http://localhost:5000/api/interview/status
   ```
   Check `"is_running"` field

3. **Can I stop current interview?**
   ```bash
   POST http://localhost:5000/api/interview/end
   ```
   Then try starting a new one

4. **Did MongoDB connect?**
   - Check backend startup logs
   - If `✅ Connected to MongoDB` → OK
   - If `⚠ MongoDB not available` → That's fine, interview still works

5. **Did audio work?**
   - Check terminal/console logs
   - Look for `🔊` emoji to see which TTS/STT was used
   - If all failed, you'll see `⚠ ... will continue without audio`
