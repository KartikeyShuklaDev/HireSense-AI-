
import sys
import io
import wave
import os
import json
import re
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import sounddevice as sd
from groq import Groq
from google import genai
from google.genai import types as ga_types
import pyttsx3  # local TTS engine
from pymongo import MongoClient  # MongoDB

# Make backend root importable
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

print("✅ Using backend root:", ROOT_DIR)

# ---- IMPORT EXISTING INTERVIEW LOGIC (RAG + Llama 4 Maverick) ----
from services.interview_service import start_interview, evaluate_answer

# ---- ELEVENLABS SERVICE (TTS + STT) ----
from services.elevenlabs_service import eleven_tts, eleven_stt

# ========================= API KEYS & CLIENTS =========================

# 🔥 Put your real keys here or via env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

client_gemini = genai.Client(api_key=GEMINI_API_KEY)
client_groq = Groq(api_key=GROQ_API_KEY)

# Local TTS engine (no quota)
engine_tts = pyttsx3.init()

# ========================= MONGODB SETUP =========================

try:
    mongo_client = MongoClient(
        "mongodb://127.0.0.1:27017", serverSelectionTimeoutMS=2000
    )
    mongo_client.admin.command("ping")
    mongo_db = mongo_client["HireSense"]
    mongo_candidates = mongo_db["CandidateData"]
    MONGO_OK = True
    print("✅ Connected to MongoDB (HireSense.CandidateData).")
except Exception as e:
    print(f"⚠ MongoDB not available: {e}")
    mongo_client = None
    mongo_db = None
    mongo_candidates = None
    MONGO_OK = False

# ========================= AUDIO SETTINGS =========================

SAMPLE_RATE = 24000
CHANNELS = 1
ANSWER_RECORD_SECONDS = 25  # time for main answers

# Flags to disable cloud TTS once they fail
GEMINI_TTS_ENABLED = True
GROQ_TTS_ENABLED = True

# HR questions file
HR_QUESTIONS_PATH = ROOT_DIR / "data" / "hr_questions.json"

# How many non-pass answers are required
HR_REQUIRED = 3
TECH_REQUIRED = 3


# ========================= HR QUESTION UTIL =========================

def pick_hr_questions(n: int = 10):
    """
    Load HR questions and return up to n random questions across allowed categories.
    Excludes:
      - salary_availability
      - final
    """
    if not HR_QUESTIONS_PATH.exists():
        raise FileNotFoundError(f"HR questions file not found at {HR_QUESTIONS_PATH}")

    with open(HR_QUESTIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    categories = data.get("categories", {})
    all_q: list[str] = []
    for cat_name, cat in categories.items():
        if cat_name in ("salary_availability", "final"):
            continue
        all_q.extend(cat.get("questions", []))

    if not all_q:
        raise ValueError("No HR questions found in hr_questions.json (after filtering).")

    import random
    random.shuffle(all_q)
    return all_q[:n]


def get_final_question() -> str:
    """
    Get 'Do you have any questions for me?' from hr_questions.json if present,
    otherwise return a default string.
    """
    if not HR_QUESTIONS_PATH.exists():
        return "Before we finish, do you have any questions for me or about this interview?"

    try:
        with open(HR_QUESTIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        final_cat = data.get("categories", {}).get("final", {})
        questions = final_cat.get("questions", [])
        if questions:
            return questions[0]
    except Exception:
        pass

    return "Before we finish, do you have any questions for me or about this interview?"


# ========================= AUDIO HELPERS =========================

def play_pcm_int16(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE):
    audio = np.frombuffer(pcm_bytes, dtype=np.int16)
    sd.play(audio, sample_rate)
    sd.wait()


def record_from_mic(duration_sec: int = ANSWER_RECORD_SECONDS) -> bytes:
    """
    Record from microphone for duration_sec seconds and return WAV bytes.
    Starts immediately after Victus finishes speaking – no extra ENTER/beep.
    """
    print(f"\n🎙 Recording for {duration_sec} seconds... speak whenever you're ready.")
    sd.default.samplerate = SAMPLE_RATE
    sd.default.channels = CHANNELS

    audio = sd.rec(int(duration_sec * SAMPLE_RATE), dtype="int16")
    sd.wait()
    print("✅ Recording complete.")

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    return buf.getvalue()


# ========================= LOCAL TTS (NO QUOTA) =========================

def local_tts_say(text: str):
    """Final fallback: OS voice via pyttsx3."""
    if not text or not text.strip():
        return

    print(f"\n🔊 [LOCAL TTS] {text}")
    try:
        engine_tts.say(text)
        engine_tts.runAndWait()
    except Exception as e:
        print(f"❌ Local TTS failed: {e}")


# ========================= TTS WITH ELEVENLABS PRIMARY =========================

def tts_say(text: str):
    """
    Speak text with this chain:
      1) ElevenLabs TTS (primary)
      2) Gemini TTS
      3) Groq TTS (playai-tts)
      4) Local TTS (pyttsx3)
    """
    global GEMINI_TTS_ENABLED, GROQ_TTS_ENABLED

    if not text or not text.strip():
        return

    print(f"\n🗣 Victus says: {text}")

    # -------- 1) ElevenLabs TTS --------
    try:
        if eleven_tts(text):
            return
        else:
            print("⚠ ElevenLabs TTS did not produce audio. Falling back to Gemini TTS...")
    except Exception as e:
        print(f"❌ ElevenLabs TTS error: {e}")
        print("➡ Falling back to Gemini TTS...")

    # -------- 2) Gemini TTS --------
    if GEMINI_TTS_ENABLED:
        try:
            resp = client_gemini.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=text,
                config=ga_types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=ga_types.SpeechConfig(
                        voice_config=ga_types.VoiceConfig(
                            prebuilt_voice_config=ga_types.PrebuiltVoiceConfig(
                                voice_name="Kore"
                            )
                        )
                    ),
                ),
            )

            audio_bytes = None
            for cand in getattr(resp, "candidates", []) or []:
                content = getattr(cand, "content", None)
                if not content:
                    continue
                for part in getattr(content, "parts", []) or []:
                    inline = getattr(part, "inline_data", None)
                    if inline and getattr(inline, "data", None):
                        audio_bytes = inline.data
                        break
                if audio_bytes:
                    break

            if not audio_bytes:
                raise Exception("Gemini TTS returned no audio parts")

            print("🔊 Gemini TTS used.")
            play_pcm_int16(audio_bytes, SAMPLE_RATE)
            return

        except Exception as e:
            print(f"⚠ Gemini TTS failed: {e}")
            GEMINI_TTS_ENABLED = False
            print("➡ Falling back to Groq TTS...")

    # -------- 3) Groq TTS --------
    if GROQ_TTS_ENABLED:
        try:
            speech = client_groq.audio.speech.create(
                model="playai-tts",
                voice="Fritz-PlayAI",
                input=text,
                response_format="wav",
            )

            wav_path = "temp_tts.wav"
            speech.write_to_file(wav_path)

            with wave.open(wav_path, "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                play_pcm_int16(frames, wf.getframerate())
            print("🔊 Groq TTS used.")
            return

        except Exception as e:
            GROQ_TTS_ENABLED = False
            print(f"❌ GROQ TTS failed: {e}")
            print("➡ Falling back to LOCAL TTS...")

    # -------- 4) Local TTS --------
    local_tts_say(text)


# ========================= STT WITH ELEVENLABS PRIMARY =========================

def stt_transcribe(wav_bytes: bytes) -> str:
    """
    Speech-to-text chain:
      1) ElevenLabs STT (primary)
      2) Gemini STT
      3) Groq Whisper
    """

    # ---- 1) ElevenLabs STT ----
    try:
        text = eleven_stt(wav_bytes)
        if text:
            print("🔊 ElevenLabs STT used.")
            return text.strip()
    except Exception as e:
        print(f"⚠ ElevenLabs STT failed: {e}")
        print("➡ Falling back to Gemini STT...")

    # ---- 2) Gemini STT ----
    try:
        resp = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                ga_types.Content(
                    parts=[
                        ga_types.Part.from_bytes(
                            data=wav_bytes, mime_type="audio/wav"
                        ),
                        ga_types.Part(
                            text=(
                                "Transcribe this audio into plain text. "
                                "Output only the transcription, no extra explanation."
                            )
                        ),
                    ]
                )
            ],
            config=ga_types.GenerateContentConfig(max_output_tokens=512),
        )

        if resp.text:
            print("🔊 Gemini STT used.")
            return resp.text.strip()

    except Exception as e:
        print(f"⚠ Gemini STT failed: {e}")
        print("➡ Falling back to Groq Whisper...")

    # ---- 3) Groq Whisper STT ----
    file_path = "temp_answer.wav"
    with open(file_path, "wb") as f:
        f.write(wav_bytes)

    try:
        transcription = client_groq.audio.transcriptions.create(
            file=open(file_path, "rb"),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            language="en",
        )
        print("🔊 Groq Whisper used.")
        return transcription.text.strip()

    except Exception as e:
        print(f"❌ Whisper STT failed: {e}")

    print("❌ All STT engines failed. Returning empty transcript.")
    return ""


# ========================= PASS / SKIP DETECTION =========================

def is_pass_answer(transcript: str) -> bool:
    """
    Check if the candidate wants to pass/skip the question.
    Triggers on phrases like:
      - 'pass this question'
      - 'pass'
      - 'sorry'
    """
    if not transcript:
        return False

    t = transcript.lower()
    if "pass this question" in t:
        return True
    if re.match(r"^\s*pass\b", t):
        return True
    if "sorry" in t:
        return True

    return False


# ========================= NAME & SKILL EXTRACTION =========================

def extract_name_from_text(transcript: str) -> str:
    """
    Simple name extractor from spoken text.
    Examples:
      'My name is Rahul'
      'I am Priya'
      'This is Kartik'
    Fallback: last alpha word.
    """
    if not transcript:
        return ""

    t = transcript.strip()
    m = re.search(r"(?:my name is|i am|this is)\s+([A-Za-z]+)", t, re.IGNORECASE)
    if m:
        return m.group(1).strip().title()

    parts = [p for p in re.split(r"\s+", t) if p.isalpha()]
    if parts:
        return parts[-1].title()

    return t.split()[0].title()


def extract_skills_from_text(transcript: str) -> list:
    """
    Parse spoken skills like 'C, Java, Python, data structures and OS'
    into a normalized skill list.
    """
    if not transcript:
        return []

    t = transcript.lower()
    skills = []

    def add(label):
        if label not in skills:
            skills.append(label)

    if "c++" in t or "cpp" in t:
        add("C++")
    if re.search(r"\bc\b", t):
        add("C")
    if "java" in t:
        add("Java")
    if "python" in t:
        add("Python")
    if "javascript" in t or "js" in t:
        add("JavaScript")
    if "mern" in t:
        add("MERN")
    if "data structure" in t or "dsa" in t:
        add("Data Structures and Algorithms")
    if "operating system" in t or "os" in t:
        add("Operating Systems")
    if "machine learning" in t or "ml" in t:
        add("Machine Learning")
    if "deep learning" in t:
        add("Deep Learning")
    if "database" in t or "sql" in t:
        add("Databases")

    if not skills:
        skills.append("general computer science")

    return skills


def save_candidate_to_mongo(name: str, skills: list, skills_raw: str):
    """Store candidate basic info in MongoDB (HireSense.CandidateData)."""
    if not MONGO_OK or mongo_candidates is None:
        print("⚠ Skipping MongoDB save (not connected).")
        return

    doc = {
        "name": name,
        "skills": skills,
        "skills_raw": skills_raw,
        "created_at": datetime.utcnow(),
    }

    try:
        mongo_candidates.insert_one(doc)
        print(f"✅ Candidate stored in MongoDB: {doc}")
    except Exception as e:
        print(f"⚠ Failed to insert candidate in MongoDB: {e}")


# ========================= MAIN INTERVIEW FLOW =========================

def main():
    print(
        "\n🎤 Victus Voice Interview (HR + Technical + RAG + Mongo)\n"
        "Pure voice conversation. No keyboard input during the flow.\n"
    )

    # ---- Victus intro ----
    tts_say(
        "Hello, I am Victus, your virtual interviewer today. "
        "We will have a short H R round followed by a technical round based on your skills and my textbooks."
    )

    # ===== GET CANDIDATE NAME BY VOICE =====
    tts_say(
        "To begin, please clearly say your name."
    )
    name_audio = record_from_mic(duration_sec=5)
    name_transcript = stt_transcribe(name_audio)
    print("\n📝 Name transcript:", name_transcript)

    candidate_name = extract_name_from_text(name_transcript)
    if not candidate_name:
        candidate_name = "Friend"

    tts_say(
        f"Nice to meet you, {candidate_name}. "
        f"I will call you {candidate_name} during this interview."
    )

    # ===== GET SKILLS BY VOICE =====
    tts_say(
        f"{candidate_name}, now tell me which programming languages or technical areas "
        "you are most comfortable with. For example C, Java, Python, data structures, "
        "operating systems or machine learning."
    )
    skills_audio = record_from_mic(duration_sec=8)
    skills_transcript = stt_transcribe(skills_audio)
    print("\n📝 Skills transcript:", skills_transcript)

    skills_list = extract_skills_from_text(skills_transcript)
    skills_str = ", ".join(skills_list)
    tts_say(
        f"Great, I heard that you are comfortable with {skills_str}. "
        "I will keep that in mind for the technical questions."
    )

    # ===== SAVE BASIC PROFILE TO MONGO =====
    save_candidate_to_mongo(candidate_name, skills_list, skills_transcript)

    # ================= HR ROUND =================
    print("\n===== HR ROUND (3 non-pass answers, no salary questions) =====")
    tts_say(
        "Let's begin with the H R round. "
        "I will ask you a series of questions. "
        "If you really want to skip one, you can say pass, but I will ask another question instead."
    )

    try:
        hr_pool = pick_hr_questions(n=10)
    except Exception as e:
        print("❌ Failed to load HR questions:", e)
        tts_say(
            "I could not load H R questions properly, "
            "so we will jump directly to the technical round."
        )
        hr_pool = []

    hr_answers = []
    hr_answered = 0
    hr_index = 0
    hr_max_loops = 30  # safety

    while hr_answered < HR_REQUIRED and hr_max_loops > 0:
        hr_max_loops -= 1

        if hr_index >= len(hr_pool):
            # refill pool if exhausted
            try:
                hr_pool = pick_hr_questions(n=10)
                hr_index = 0
            except Exception as e:
                print("❌ Could not refill HR questions:", e)
                break

        if not hr_pool:
            break

        q = hr_pool[hr_index]
        hr_index += 1

        print(f"\n[HR Q] {q}")
        tts_say(q)

        # Directly start listening
        wav_bytes = record_from_mic(duration_sec=ANSWER_RECORD_SECONDS)

        print("\n⏳ Transcribing your H R answer...")
        transcript = stt_transcribe(wav_bytes)
        print("\n📝 Your HR Answer:\n", transcript)

        if is_pass_answer(transcript):
            tts_say(
                "Alright, we will not consider this question. "
                "I will ask you a different one."
            )
            hr_answers.append({"question": q, "answer": transcript, "skipped": True})
            continue

        hr_answers.append({"question": q, "answer": transcript, "skipped": False})
        hr_answered += 1

        if transcript.strip():
            tts_say("Thank you for sharing that.")
        else:
            tts_say(
                "I could not clearly hear your answer, but let's keep going."
            )

    # ================= TECHNICAL ROUND =================
    print("\n===== TECHNICAL ROUND (3 evaluated answers from RAG) =====")
    tts_say(
        "Now we will move to the technical round. "
        "These questions are based on your skills and the textbooks I have read. "
        "If you say pass or sorry, I will ask another question, but you still need to answer three questions."
    )

    topic_hint = skills_str if skills_list else "computer science"

    tech_results = []
    total_score = 0
    tech_answered = 0
    questions_buffer = []
    q_index = 0
    tech_max_loops = 50  # safety

    while tech_answered < TECH_REQUIRED and tech_max_loops > 0:
        tech_max_loops -= 1

        # refill buffer if empty or exhausted
        if q_index >= len(questions_buffer):
            try:
                print("\n⏳ Fetching technical questions from RAG...")
                interview_data = start_interview(
                    topic=topic_hint,
                    num_questions=3,
                    random_from_rag=True,
                )
            except Exception as e:
                print(f"❌ Error starting technical interview: {e}")
                tts_say(
                    "I encountered an error while generating more technical questions. "
                    "We will stop here."
                )
                break

            if not isinstance(interview_data, dict):
                print("❌ start_interview() returned invalid data:", interview_data)
                tts_say(
                    "I received invalid data from the question generator. "
                    "We will stop here."
                )
                break

            questions_buffer = interview_data.get("questions") or []
            global_sources = interview_data.get("global_sources", [])
            q_index = 0

            if not questions_buffer:
                print("❌ No technical questions were generated by the backend.")
                print("   Raw interview_data:", interview_data)
                tts_say(
                    "No technical questions were generated. "
                    "We will stop here."
                )
                break

        q = questions_buffer[q_index]
        q_index += 1

        qid = q.get("id")
        qtext = q.get("question")
        ideal = q.get("ideal_answer")
        q_sources = q.get("sources", global_sources)

        print(f"\n[TECH Q] {qtext}")
        print("\n📚 Sources:")
        for src in q_sources:
            print(" -", src)

        tts_say(qtext)

        # Listen immediately
        wav_bytes = record_from_mic(duration_sec=ANSWER_RECORD_SECONDS)

        print("\n⏳ Transcribing your answer...")
        transcript = stt_transcribe(wav_bytes)
        print("\n📝 You said:\n", transcript)

        if is_pass_answer(transcript):
            tts_say(
                "Okay, I will not evaluate this one. "
                "Let me ask you another technical question."
            )
            continue  # do not increment tech_answered

        if not transcript.strip():
            tts_say(
                "I could not clearly hear your answer, but I will still try to evaluate what I got."
            )

        print("\n⏳ Evaluating your answer...")
        try:
            eval_res = evaluate_answer(
                question_id=qid,
                question_text=qtext,
                ideal_answer=ideal,
                user_answer=transcript,
            )
        except Exception as e:
            print(f"❌ Error in evaluation for a technical question: {e}")
            tts_say(
                "There was an error while evaluating this answer. "
                "We will move to another question."
            )
            continue

        score = eval_res.get("score", 0)
        feedback = eval_res.get("feedback", "")
        missing_points = eval_res.get("missing_points", [])
        eval_sources = eval_res.get("sources", [])
        reliability = eval_res.get("reliability_score", 0)
        grounded = eval_res.get("grounded_in_context", False)

        total_score += score
        tech_answered += 1
        tech_results.append(eval_res)

        print("\n🎯 RESULT FOR THIS QUESTION")
        print("---------------------------")
        print(f"Score: {score}/100")
        print(f"Reliability: {reliability}/100")
        print(f"Grounded in context: {grounded}")
        print(f"Feedback: {feedback}")
        if missing_points:
            print("Missing points:")
            for mp in missing_points:
                print("  -", mp)

        if eval_sources:
            print("\n📚 Evaluation context was taken from:")
            for src in eval_sources:
                print(" -", src)

        tts_say(f"For this question, your score is {score} out of 100. {feedback}")

    # ================= SUMMARY & FINAL QUESTION =================
    if tech_answered > 0:
        avg_score = total_score / tech_answered
    else:
        avg_score = 0

    summary = (
        f"{candidate_name}, this brings us to the end of your technical round. "
        f"Based on the answers I evaluated, your average score is {int(avg_score)} out of 100."
    )

    print("\n===== INTERVIEW SUMMARY =====")
    print(summary)
    tts_say(summary)

    # Final “Any questions for us?” question
    final_q = get_final_question()
    print("\n[FINAL] ", final_q)
    tts_say(
        "Before we finish, I have one last question for you."
    )
    tts_say(final_q)
    tts_say("You can speak freely now, and I will listen.")

    final_audio = record_from_mic(duration_sec=15)
    final_transcript = stt_transcribe(final_audio)
    print("\n📝 Candidate's final question/comment:\n", final_transcript)

    tts_say(
        "Thank you for your time and for taking this mock interview with me. "
        "This session is now complete. I wish you all the best for your real interviews."
    )


if __name__ == "__main__":
    main()
