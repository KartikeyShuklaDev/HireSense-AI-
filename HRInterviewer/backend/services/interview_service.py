from typing import Dict, Any, List

from services.rag_service import (
    get_relevant_chunks_with_sources,
    get_random_chunks_with_sources,
)
from services.gemini_service import (
    generate_questions_from_context,
    evaluate_with_gemini,
)


def start_interview(
    topic: str,
    num_questions: int = 5,
    random_from_rag: bool = False,
) -> Dict[str, Any]:
    """
    Start an interview.

    If random_from_rag = True:
      - ignore topic, sample random chunks from RAG (all books),
      - generate questions from that random context.

    Else:
      - use topic to search RAG and generate questions from relevant chunks.

    Each question will include a 'sources' field listing book filenames
    from which its context was taken.
    """

    if random_from_rag:
        chunks = get_random_chunks_with_sources(num_chunks=12)
        topic_used = "RAG_RANDOM"
    else:
        if not topic or not isinstance(topic, str):
            topic = "data structures"
        chunks = get_relevant_chunks_with_sources(topic=topic, top_k=12)
        topic_used = topic

    if not chunks:
        raise RuntimeError("No context chunks found from RAG.")

    context_text = "\n\n".join(c["text"] for c in chunks)
    sources = sorted({c["source"] for c in chunks})

    # generate interview questions strictly from context
    questions = generate_questions_from_context(
        context_text=context_text,
        num_questions=num_questions,
        topic=topic_used,
    )

    # attach sources to each question
    for q in questions:
        q["sources"] = sources

    return {
        "topic": topic_used,
        "questions": questions,
        "global_sources": sources,  # shared sources for whole set
    }


def evaluate_answer(
    question_id: int,
    question_text: str,
    ideal_answer: str,
    user_answer: str,
) -> Dict[str, Any]:
    """
    Evaluate one answer with RAG context + Gemini.
    """
    if not question_text or not ideal_answer or not user_answer:
        raise ValueError("question_text, ideal_answer, and user_answer are required.")

    # For evaluation, use question as query to RAG
    eval_chunks = get_relevant_chunks_with_sources(topic=question_text, top_k=8)
    eval_context = "\n\n".join(c["text"] for c in eval_chunks)

    evaluation = evaluate_with_gemini(
        question_text=question_text,
        ideal_answer=ideal_answer,
        user_answer=user_answer,
        context_text=eval_context,
    )

    evaluation["question_id"] = question_id
    evaluation["sources"] = sorted({c["source"] for c in eval_chunks})

    return evaluation
