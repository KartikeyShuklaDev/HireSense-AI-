# backend/services/gemini_service.py

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAjXIAr-Agp-MRCvJ9v-Al0")

import json
import re
import os
from typing import List, Dict, Any, Optional

from google import genai
from google.genai import types as ga_types
from groq import Groq

# =========================================================
# API KEYS & CLIENTS
# =========================================================

# Gemini key (for question generation + fallback eval)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Groq key (for Maverick evaluation + fallback question gen)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # <-- replace or set env
try:
    groq_client: Optional[Groq] = Groq(api_key=GROQ_API_KEY)
except Exception:
    groq_client = None


# =========================================================
# LOW-LEVEL HELPERS
# =========================================================

def _get_text_from_gemini_response(resp: Any) -> str:
    """
    Robustly extract text from a Gemini response.
    Does NOT rely only on resp.text.
    """
    if not hasattr(resp, "candidates") or not resp.candidates:
        return ""

    texts: List[str] = []

    for cand in resp.candidates:
        content = getattr(cand, "content", None)
        if not content or not getattr(content, "parts", None):
            continue
        for part in content.parts:
            t = getattr(part, "text", None)
            if t:
                texts.append(t)

    return "\n".join(texts).strip()


def _extract_json_strict(text: str) -> Any:
    """
    Parse JSON from a string that is EXPECTED to be pure JSON.
    Raises ValueError if it fails.
    """
    if not text:
        raise ValueError("Empty text while JSON was expected.")
    return json.loads(text)


def _extract_json_loose(text: str) -> Any:
    """
    For LLM outputs that might contain some extra text or ```json fences.
    Tries to find the JSON part and parse it.
    Raises ValueError if it cannot parse.
    """
    if not text:
        raise ValueError("Empty text while JSON was expected.")

    t = text.strip()

    # Remove ```json ... ``` if present
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].strip()

    # Try direct first
    try:
        return json.loads(t)
    except Exception:
        pass

    # Try to extract the first {...} block
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = t[start : end + 1]
        return json.loads(candidate)

    # If still failing:
    raise ValueError("Could not parse JSON from LLM output.")


# =========================================================
# QUESTION GENERATION (Gemini + Groq fallback)
# =========================================================

def _fallback_questions_from_context(
    context_text: str,
    num_questions: int,
    topic: str,
) -> List[Dict]:
    """
    Local fallback when Gemini & Groq don't return usable JSON.
    We create simple 'Explain this' style questions from the context,
    so your interview DOES NOT CRASH.
    """
    raw = context_text.replace("\n", " ").strip()
    if not raw:
        raw = f"Explain the basics of {topic}."

    # crude sentence split
    sentences = re.split(r"(?<=[.!?])\s+", raw)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if not sentences:
        sentences = [f"Explain the basics of {topic}."]

    questions: List[Dict] = []
    for i in range(num_questions):
        s = sentences[i % len(sentences)]
        q_text = f"Explain the following concept in detail: {s}"
        questions.append(
            {
                "id": i + 1,
                "question": q_text,
                "ideal_answer": "Refer to the textbook explanation of this concept.",
            }
        )
    return questions


def _groq_chat(
    system_instruction: str,
    user_prompt: str,
    max_tokens: int = 2048,
    temperature: float = 0.3,
) -> str:
    """
    Call Groq LLM (Maverick or similar) and return content.
    """
    if groq_client is None:
        raise RuntimeError("Groq client not initialized (no API key).")

    resp = groq_client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_completion_tokens=max_tokens,
        top_p=1,
        stream=False,
    )

    if not resp.choices:
        return ""

    return (resp.choices[0].message.content or "").strip()


def generate_questions_from_context(
    context_text: str,
    num_questions: int = 5,
    topic: str = "data structures",
) -> List[Dict]:
    """
    Use Gemini primarily to generate interview questions + ideal answers
    strictly based on the given textbook context.

    Fallback order:
      1) Gemini (JSON)
      2) Groq Maverick (JSON)
      3) Local simple questions from context
    """

    system_instruction = (
        "You are an expert technical interviewer for computer science. "
        "You generate clear, focused technical interview questions using ONLY the provided context. "
        "Do not introduce topics that are not present in the context."
    )

    prompt = f"""
Context from CS textbooks (DSA, OS, Programming, ML, etc.):

\"\"\"{context_text[:12000]}\"\"\"


Task:
Generate {num_questions} technical interview questions for the topic: {topic}.

Rules:
- Use ONLY the information present in the context.
- Questions should be suitable for an oral technical interview.
- For each question, provide an 'ideal_answer' that is precise and correct.
- Return ONLY JSON. No extra explanations.

JSON format:
[
  {{
    "id": 1,
    "question": "<question text>",
    "ideal_answer": "<ideal answer text>"
  }},
  ...
]
"""

    # ---------- 1) Try Gemini ----------
    try:
        resp = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=ga_types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )

        raw = _get_text_from_gemini_response(resp)
        if raw:
            data = _extract_json_loose(raw)
            for i, q in enumerate(data, start=1):
                q["id"] = i
            return data

    except Exception:
        pass  # fallthrough to Groq

    # ---------- 2) Try Groq ----------
    try:
        if groq_client is not None:
            raw = _groq_chat(
                system_instruction=system_instruction,
                user_prompt=prompt,
                max_tokens=2048,
                temperature=0.3,
            )
            if raw:
                data = _extract_json_loose(raw)
                for i, q in enumerate(data, start=1):
                    q["id"] = i
                return data
    except Exception:
        pass  # fallthrough to local fallback

    # ---------- 3) Local fallback ----------
    return _fallback_questions_from_context(context_text, num_questions, topic)


# =========================================================
# ANSWER EVALUATION (Groq Maverick + RAG + reliability)
# =========================================================

def evaluate_with_gemini(
    question_text: str,
    ideal_answer: str,
    user_answer: str,
    context_text: str = "",
) -> Dict:
    """
    Evaluate the candidate's answer vs the ideal answer + textbook context (RAG).

    Primary evaluator:
      - Groq LLM: meta-llama/llama-4-maverick-17b-128e-instruct

    It returns a dict with at least:
      - score: int (0–100)
      - feedback: str
      - missing_points: List[str]
      - reliability_score: int (0–100)   -> how confident the model is
      - grounded_in_context: bool        -> is the answer based on the provided context?
      - reasoning: str                   -> short explanation of how it judged

    Fallback if Groq fails:
      - Use a simpler Gemini-based text format and regex parse (older logic).
      - If that also fails, return a safe default with score=0.
    """

    # ------------------ Groq Maverick primary eval ------------------
    system_instruction = (
        "You are a strict but fair technical interviewer for computer science. "
        "You compare the student's answer against the ideal answer and the textbook context. "
        "You must:\n"
        "- Judge conceptual correctness and completeness.\n"
        "- Judge how well the answer matches the provided textbook context (groundedness).\n"
        "- Avoid hallucinating new facts not supported by context unless clearly stated.\n"
        "- Be concise but specific."
    )

    user_prompt = f"""
You are evaluating a technical CS interview answer.

Question:
\"\"\"{question_text}\"\"\"


Ideal answer (from textbooks or reference solution):
\"\"\"{ideal_answer}\"\"\"


Student answer (transcribed from speech, may contain minor errors):
\"\"\"{user_answer}\"\"\"


Additional textbook context from RAG (this is the ground truth you must rely on):
\"\"\"{context_text[:8000]}\"\"\"


Your tasks:
1. Compare the student answer with the ideal answer AND the textbook context.
2. Decide how accurate and complete the student answer is.
3. Judge how well the answer is grounded in the given context (does it rely on the same concepts,
   or does it invent things that are not supported?).
4. Provide a reliability score for your own evaluation: how confident are you (0–100)?

Return ONLY valid JSON (no markdown, no ``` fences) with this exact schema:

{{
  "score": <integer between 0 and 100>,              // accuracy / quality of the answer
  "feedback": "<2-5 sentences of feedback>",         // constructive, concise
  "missing_points": [                                // list of short bullet items of missing or weak points
    "<point 1>",
    "<point 2>"
  ],
  "reliability_score": <integer between 0 and 100>,  // how confident you are in this evaluation
  "grounded_in_context": <true or false>,            // true if student answer mostly aligns with context
  "reasoning": "<short explanation of how you decided the score and reliability>"
}}
"""

    # Try Groq Maverick first
    try:
        if groq_client is not None:
            raw = _groq_chat(
                system_instruction=system_instruction,
                user_prompt=user_prompt,
                max_tokens=900,
                temperature=0.2,
            )
            if raw:
                data = _extract_json_strict(raw)

                # normalize and clamp a bit
                score = int(data.get("score", 0))
                score = max(0, min(100, score))

                reliability = int(data.get("reliability_score", 0))
                reliability = max(0, min(100, reliability))

                feedback = str(data.get("feedback", "")).strip() or \
                    "Evaluation completed, but no detailed feedback provided."

                missing_points_raw = data.get("missing_points") or []
                if isinstance(missing_points_raw, list):
                    missing_points = [str(p).strip() for p in missing_points_raw if str(p).strip()]
                else:
                    missing_points = []

                grounded = bool(data.get("grounded_in_context", False))
                reasoning = str(data.get("reasoning", "")).strip()

                return {
                    "score": score,
                    "feedback": feedback,
                    "missing_points": missing_points,
                    "reliability_score": reliability,
                    "grounded_in_context": grounded,
                    "reasoning": reasoning,
                }

    except Exception as e:
        print(f"⚠ Groq Maverick evaluation failed or JSON invalid: {e}")

    # ------------------ Gemini fallback (text format) ------------------
    # Keep your older, simpler text format as a backup so system never dies.

    fallback_system_instruction = (
        "You are a strict but fair technical interviewer for computer science. "
        "You compare the student's answer against the ideal answer and the textbook context. "
        "Focus on conceptual correctness and completeness, not grammar."
    )

    fallback_prompt = f"""
You are evaluating a technical CS interview answer.

Question:
\"\"\"{question_text}\"\"\"


Ideal answer (from textbooks):
\"\"\"{ideal_answer}\"\"\"


Student answer (transcribed from speech, may contain minor errors):
\"\"\"{user_answer}\"\"\"


Additional textbook context (for reference):
\"\"\"{context_text[:8000]}\"\"\"


Respond in EXACTLY this format:

Score: <integer between 0 and 100>
Feedback: <2-4 sentences of feedback>
Missing points:
- <short bullet with an important missing or weak point>
- <another point>
- ...

Do NOT add any extra sections.
"""

    def _parse_text_eval(text: str) -> Dict:
        if not text:
            return {
                "score": 0,
                "feedback": "Model did not return an evaluation.",
                "missing_points": [],
                "reliability_score": 0,
                "grounded_in_context": False,
                "reasoning": "",
            }

        # --- Parse score ---
        score_match = re.search(r"Score\s*:\s*(\d+)", text, re.IGNORECASE)
        if score_match:
            score_val = int(score_match.group(1))
            score_val = max(0, min(100, score_val))
        else:
            score_val = 0

        # --- Split sections ---
        feedback = ""
        missing_points: List[str] = []

        fb_match = re.search(r"Feedback\s*:(.*)", text, re.IGNORECASE | re.DOTALL)
        if fb_match:
            fb_and_rest = fb_match.group(1).strip()
        else:
            fb_and_rest = ""

        mp_index = fb_and_rest.lower().find("missing points")
        if mp_index != -1:
            feedback = fb_and_rest[:mp_index].strip()
            mp_block = fb_and_rest[mp_index:].split("\n", 1)
            if len(mp_block) > 1:
                mp_lines_raw = mp_block[1].splitlines()
            else:
                mp_lines_raw = []
        else:
            feedback = fb_and_rest.strip()
            mp_lines_raw = []

        for line in mp_lines_raw:
            line = line.strip()
            if line.startswith("-") or line.startswith("*"):
                mp = line[1:].strip()
                if mp:
                    missing_points.append(mp)

        if not feedback:
            feedback = "Evaluation completed, but detailed feedback could not be parsed."

        # In fallback we can't know reliability/groundedness precisely
        return {
            "score": score_val,
            "feedback": feedback,
            "missing_points": missing_points,
            "reliability_score": 0,
            "grounded_in_context": False,
            "reasoning": "Fallback Gemini evaluation used because Groq evaluation failed.",
        }

    try:
        resp = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=fallback_prompt,
            config=ga_types.GenerateContentConfig(
                system_instruction=fallback_system_instruction,
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
        text = _get_text_from_gemini_response(resp)
        if text:
            return _parse_text_eval(text)

    except Exception as e:
        print(f"⚠ Gemini fallback evaluation failed: {e}")

    # ------------------ Final safe fallback ------------------
    return {
        "score": 0,
        "feedback": "Evaluation failed due to an internal error. Please try again.",
        "missing_points": [],
        "reliability_score": 0,
        "grounded_in_context": False,
        "reasoning": "Both Groq and Gemini evaluation failed.",
    }
