# import os, json, asyncio
# from typing import Dict
# from bson import ObjectId
# from database.connection import db
# from ollama import AsyncClient
# from dotenv import load_dotenv
# from services.app_error import AppError 

# load_dotenv()

# OLLAMA_HOST = os.getenv("OLLAMA_HOST")
# MODEL = os.getenv("RESUME_MODEL")

# ollama = AsyncClient(host=OLLAMA_HOST)

# SKILL_SEMAPHORE = asyncio.Semaphore(int(os.getenv("SKILL_SEMAPHORE", 5)))

# SKILL_MATCH_PROMPT = """
# Task: ATS Skill Matcher

# Rules:
# - Case-insensitive
# - Match synonyms (JS = JavaScript, Node = Node.js, etc.)
# - Be flexible (partial matches allowed)
# - Count UNIQUE matches only
# - Do NOT hallucinate

# Must-Have: {must_have}
# Good-To-Have: {good_to_have}
# Resume: {resume_skills}

# Return ONLY JSON:
# {{
#   "matched_must_have": int,
#   "matched_good_to_have": int
# }}
# """
# async def llm_match_resume_skills(job: dict, resume: dict):

#     ollama = AsyncClient(host=OLLAMA_HOST)
#     if not OLLAMA_HOST:
#         raise AppError("OLLAMA_HOST is not configured", 500)

#     if not MODEL:
#         raise AppError("RESUME_MODEL is not configured", 500)

#     jd= job

#     must_have = jd.get("mustHave", [])
#     good_to_have = jd.get("goodToHave", [])

#     resume_skills = (
#         resume.get("summaryForAI", {})
#         .get("skills", [])
#     )
#     if not resume_skills:
#         raise AppError("Resume skills not found")

#     prompt = SKILL_MATCH_PROMPT.format(
#         must_have=must_have,
#         good_to_have=good_to_have,
#         resume_skills=resume_skills
#     )

#     try:
#         async with SKILL_SEMAPHORE:

#             response = await ollama.chat(
#                 model=MODEL,
#                 messages=[
#                     {"role": "system", "content": "Return only valid JSON."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 options={"temperature": 0}
#             )

#         raw = response["message"]["content"].strip()
#         raw = raw.replace("```json", "").replace("```", "").strip()

    
#         if not raw:
#             raise AppError("LLM returned empty response for skill matching", 500)

#         parsed = json.loads(raw)
    
#         if not isinstance(parsed, dict):
#             raise AppError("Invalid LLM response format for skill matching", 500)

#         matched_must_have = parsed.get("matched_must_have")
#         matched_good_to_have = parsed.get("matched_good_to_have")

#         if not isinstance(matched_must_have, int) or not isinstance(matched_good_to_have, int):
#             raise AppError("LLM returned invalid skill match counts", 500)

#         return {
#             "matched_must_have": matched_must_have,
#             "matched_good_to_have": matched_good_to_have
#         }

#     except AppError:
#         raise

#     except Exception as e:
#         raise AppError(f"Skill LLM matching failed: {str(e)}", 500)


import os, json, asyncio
from typing import Dict
from bson import ObjectId
from database.connection import db
from dotenv import load_dotenv
from services.app_error import AppError
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("RESUME_MODEL")

SKILL_SEMAPHORE = asyncio.Semaphore(int(os.getenv("SKILL_SEMAPHORE", 5)))

SKILL_MATCH_PROMPT = """
Task: ATS Skill Matcher

Rules:
- Case-insensitive
- Match synonyms (JS = JavaScript, Node = Node.js, etc.)
- Be flexible (partial matches allowed)
- Count UNIQUE matches only
- Do NOT hallucinate

Must-Have: {must_have}
Good-To-Have: {good_to_have}
Resume: {resume_skills}

Return ONLY JSON:
{{
  "matched_must_have": int,
  "matched_good_to_have": int
}}
"""


async def llm_match_resume_skills(job: dict, resume: dict):

    if not os.getenv("GROQ_API_KEY"):
        raise AppError("GROQ_API_KEY is not configured", 500)

    jd = job

    must_have = jd.get("mustHave", [])
    good_to_have = jd.get("goodToHave", [])

    resume_skills = (
        resume.get("summaryForAI", {})
        .get("skills", [])
    )

    if not resume_skills:
        raise AppError("Resume skills not found", 400)

    prompt = SKILL_MATCH_PROMPT.format(
        must_have=must_have,
        good_to_have=good_to_have,
        resume_skills=resume_skills
    )

    try:
        async with SKILL_SEMAPHORE:

            # 🔥 GROQ CALL (sync inside async - OK for now)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

        raw = response.choices[0].message.content.strip()

        # Clean response
        raw = raw.replace("```json", "").replace("```", "").strip()

        if not raw:
            raise AppError("LLM returned empty response for skill matching", 500)

        parsed = json.loads(raw)

        if not isinstance(parsed, dict):
            raise AppError("Invalid LLM response format for skill matching", 500)

        matched_must_have = parsed.get("matched_must_have")
        matched_good_to_have = parsed.get("matched_good_to_have")

        if not isinstance(matched_must_have, int) or not isinstance(matched_good_to_have, int):
            raise AppError("LLM returned invalid skill match counts", 500)

        return {
            "matched_must_have": matched_must_have,
            "matched_good_to_have": matched_good_to_have
        }

    except AppError:
        raise

    except Exception as e:
        raise AppError(f"GROQ skill matching failed: {str(e)}", 500)