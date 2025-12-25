import sys
from pathlib import Path

# Ensure backend root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

print("✅ Loaded test_interview_cli.py from", ROOT_DIR)

from services.interview_service import start_interview, evaluate_answer


def main():
    print("\n🔹 HR Interviewer CLI Test")
    print("This will use your RAG (books) + Gemini to take a small interview.\n")

    topic = input("Enter interview topic (default: 'data structures'): ").strip()
    if not topic:
        topic = "data structures"

    try:
        num_questions = 3
        print(f"\n⏳ Generating {num_questions} questions for topic: {topic} ...")
        interview_data = start_interview(topic=topic, num_questions=num_questions)
    except Exception as e:
        print(f"\n❌ Error starting interview: {e}")
        return

    questions = interview_data.get("questions", [])
    if not questions:
        print("\n❌ No questions returned. Check RAG and Gemini configuration.")
        return

    print(f"\n✅ Interview started on topic: {topic}")
    print(f"Total questions: {len(questions)}")
    print("-" * 60)

    total_score = 0
    results = []

    for q in questions:
        qid = q.get("id")
        qtext = q.get("question")
        ideal = q.get("ideal_answer")

        print(f"\nQuestion {qid}: {qtext}")
        print("(Type your answer below. This simulates your spoken answer.)\n")
        user_answer = input("Your answer: ").strip()

        if not user_answer:
            user_answer = ""

        try:
            print("\n⏳ Evaluating your answer with Gemini...")
            evaluation = evaluate_answer(
                question_id=qid,
                question_text=qtext,
                ideal_answer=ideal,
                user_answer=user_answer,
            )
        except Exception as e:
            print(f"❌ Error evaluating answer: {e}")
            continue

        score = evaluation.get("score", 0)
        feedback = evaluation.get("feedback", "")
        missing_points = evaluation.get("missing_points", [])

        total_score += score
        results.append(evaluation)

        print(f"\n🧮 Score for this question: {score}/100")
        print(f"💬 Feedback: {feedback}")
        if missing_points:
            print("❗ Missing / weak points:")
            for mp in missing_points:
                print(f"   - {mp}")

        print("-" * 60)

    if results:
        avg_score = total_score / len(results)
        print(f"\n🎯 Final average score: {avg_score:.1f}/100")
    else:
        print("\n❌ No questions were evaluated.")


if __name__ == "__main__":
    print("▶ Starting CLI interview script...")
    main()
