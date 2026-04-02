import os, re, json
from datetime import datetime
from dotenv import load_dotenv
from ollama import AsyncClient
from services.app_error import AppError

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST")
MODEL = os.getenv("RESUME_MODEL")
ollama = AsyncClient(host=OLLAMA_HOST)

def normalize_experience(exp):
    return {
        "type": str(exp.get("type") or "").lower(),
        "duration": exp.get("duration") or "",
        "start": exp.get("start") or None,
        "end": exp.get("end") or None,
        "text": exp.get("text") or ""
    }

def parse_duration_to_months(duration: str) -> int:
    if not duration:
        return 0

    duration = str(duration).lower()

    try:
        years = re.search(r"(\d+)\s*year", duration)
        months = re.search(r"(\d+)\s*month", duration)

        total = 0

        if years:
            total += int(years.group(1)) * 12

        if months:
            total += int(months.group(1))

        return total
    except:
        return 0

def safe_date(date_str):
    """
    Safely convert date string to datetime for sorting
    """
    if not date_str:
        return datetime.min

    date_str = str(date_str).lower()

    if date_str == "present":
        return datetime.max

    try:
        return datetime.strptime(date_str[:7], "%Y-%m")
    except:
        return datetime.min


async def score_experience_relevance(experience: dict, jd_text: str) -> dict:

    prompt = f"""
You are an ATS system evaluating whether a candidate's experience is relevant to a job description.

Be REASONABLE:
- If experience is PARTIALLY relevant (same domain, backend, APIs, Python), consider it relevant
- Do NOT be overly strict
- Only reject if completely unrelated (e.g., sales, marketing)

Job Description:
{jd_text}

Candidate Experience:
Duration: {experience.get("duration", "")}  
Description: {experience.get("text", "")}

Return ONLY JSON:

If relevant:
{{
  "duration": "{experience.get("duration", "")}"
}}

If NOT relevant:
{{}}
"""

    try:
        response = await ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0}
        )

        raw = response["message"]["content"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        if not raw:
            return {}

        result = json.loads(raw)

        return result if isinstance(result, dict) and result else {}

    except Exception as e:
       raise AppError(f"LLM relevance scoring failed: {str(e)}", 500)



async def get_relevant_experiences(resume: dict, jd: dict) -> dict:

    experiences = resume.get("summaryForAI", {}).get("experience", [])
    jd_text = jd.get("experience", {}).get("experienceText", "")

    experiences = [normalize_experience(e) for e in experiences if isinstance(e, dict)]

    relevant_experiences = []

    total_months = 0
    full_time_months = 0
    internship_months = 0

    for exp in experiences:

        if not isinstance(exp, dict):
            continue

        result = await score_experience_relevance(exp, jd_text)

        if not result:
            continue

        months = parse_duration_to_months(result.get("duration", ""))
        exp_type = str(exp.get("type", "")).lower()

        total_months += months

        if exp_type == "full_time":
            full_time_months += months
        elif exp_type == "internship":
            internship_months += months

        relevant_experiences.append({
            "type": exp_type,
            "duration": exp.get("duration", ""),
            "months": months,
            "start": exp.get("start"),
            "end": exp.get("end")
        })

    relevant_experiences = sorted(
        relevant_experiences,
        key=lambda x: safe_date(x.get("end")),
        reverse=True
    )

    return {
        "relevant_experiences": relevant_experiences,
        "total_relevant_years": round(total_months / 12, 2),
        "full_time_years": round(full_time_months / 12, 2),
        "internship_years": round(internship_months / 12, 2)
    }


