from groq import Groq

try:
    from config import GROQ_API_KEY, GROQ_MODEL
except Exception:  # noqa: BLE001 - allow running standalone
    import os
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

client = Groq(api_key=GROQ_API_KEY)

def rewrite_answer(question, transcript):
    prompt = f"""You are an expert interview coach.

A candidate was asked: "{question}"

Their answer was: "{transcript}"

Rewrite their answer to be more confident, structured, and professional.
Use the STAR method where applicable. Keep it 3 to 5 sentences.
Return only the rewritten answer, no explanation."""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate rewrite: {str(e)}"


def ideal_answer_analysis(question, transcript):
    """
    Produce a structured 'ideal answer' comparison for the analysis page:
    ideal answer, what the candidate did well, what to improve, missing points,
    and phrases/areas to avoid. Returns a dict; degrades gracefully on error.
    """
    prompt = f"""You are an expert interview coach. Return ONLY valid JSON.

Question: "{question}"
Candidate's answer: "{transcript}"

Return a JSON object with exactly these keys:
"ideal_answer": a strong 3-5 sentence model answer using the STAR method where applicable,
"did_well": array of 2-4 short strings on what the candidate did well,
"improve": array of 2-4 short strings on what could be improved,
"missing_points": array of 1-4 short strings on important points the candidate missed,
"avoid": array of 1-3 short strings on phrases or areas to avoid.
Do not include any text outside the JSON object."""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:  # noqa: BLE001
        return {
            "ideal_answer": rewrite_answer(question, transcript),
            "did_well": [],
            "improve": [],
            "missing_points": [],
            "avoid": [],
            "error": str(e),
        }