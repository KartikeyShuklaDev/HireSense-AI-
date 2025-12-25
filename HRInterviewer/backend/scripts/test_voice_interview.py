import sys
import os
from pathlib import Path

# Make sure backend root is importable
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

print("✅ Using backend root:", ROOT_DIR)

from services.interview_service import start_interview, evaluate_answer
from services.speech_service import tts_interviewer, transcribe_audio_bytes


def main():
    print("\n🎤 HR Voice Interviewer Test (Local, No HTTP)")
    print("This will:\n"
          "  1) Generate questions from your books (RAG + Gemini)\n"
          "  2) Speak the first question as audio\n"
          "  3) Let you record an answer and save as a WAV\n"
          "  4) Transcribe and evaluate your answer\n")

    topic = input("Enter interview topic (default: 'data structures'): ").strip()
    if not topic:
        topic = "data structures"

    # 1) Generate questions from RAG + Gemini
    try:
        num_questions = 1
        print(f"\n⏳ Generating {num_questions} question for topic: {topic} ...")
        interview_data = start_interview(topic=topic, num_questions=num_questions)
    except Exception as e:
        print(f"\n❌ Error starting interview: {e}")
        return

    questions = interview_data.get("questions", [])
    if not questions:
        print("\n❌ No questions returned. Check RAG / Gemini config.")
        return

    q = questions[0]
    qid = q.get("id")
    qtext = q.get("question")
    ideal = q.get("ideal_answer")

    print(f"\n✅ Question generated from your books:\n  Q{qid}: {qtext}")

    # 2) TTS: speak the question
    try:
        print("\n⏳ Generating interviewer audio (TTS)...")
        audio_path = tts_interviewer(text=qtext)
        print(f"✅ Audio generated at:\n  {audio_path}")
        print("👉 Open this file in your audio player to listen to the interviewer.")
        # On Windows, auto-open the file (optional)
        if os.name == "nt":
            try:
                os.startfile(audio_path)
                print("🔊 Attempted to auto-open the audio file in default player.")
            except Exception as e:
                print(f"⚠ Could not auto-open audio file: {e}")
    except Exception as e:
        print(f"\n❌ Error generating TTS audio: {e}")
        return

    # 3) Ask user to record answer and give path
    print("\n🎙 Now record your answer to that question using any recorder.")
    print("   Save it as a WAV file (e.g., answer.wav).")
    answer_path = input("Enter full path to your answer WAV file: ").strip()

    if not answer_path:
        print("❌ No file path provided. Exiting.")
        return

    answer_file = Path(answer_path)
    if not answer_file.exists():
        print(f"❌ File does not exist: {answer_file}")
        return

    # 4) STT: transcribe the audio
    try:
        print("\n⏳ Transcribing your audio answer with Gemini...")
        audio_bytes = answer_file.read_bytes()
        transcript = transcribe_audio_bytes(audio_bytes, mime_type="audio/wav")
    except Exception as e:
        print(f"\n❌ Error during transcription: {e}")
        return

    print(f"\n📝 Transcript of your answer:\n  {transcript}")

    # 5) Evaluate the transcript as the user's answer
    try:
        print("\n⏳ Evaluating your answer (RAG + Gemini)...")
        evaluation = evaluate_answer(
            question_id=qid,
            question_text=qtext,
            ideal_answer=ideal,
            user_answer=transcript,
        )
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        return

    score = evaluation.get("score", 0)
    feedback = evaluation.get("feedback", "")
    missing_points = evaluation.get("missing_points", [])

    print("\n🎯 Evaluation Result")
    print("---------------------")
    print(f"Question: {qtext}")
    print(f"Your transcript: {transcript}")
    print(f"\nScore: {score}/100")
    print(f"Feedback: {feedback}")
    if missing_points:
        print("\nMissing / weak points:")
        for mp in missing_points:
            print(f"  - {mp}")
    print("\n✅ Voice interviewer test complete.\n")


if __name__ == "__main__":
    main()
