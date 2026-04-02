import json
from typing import Any, Dict
from services.app_error import AppError

from database.connection import db
from model.JD_schema import JDInput
from utils.JD_prompt import jd_structuring_prompt
from controller.summary.jd_helper import call_llm, clean_skill_list

collection = db["jobdescriptions"]


async def process_jd(payload: JDInput) -> Dict[str, Any]:
    try:
        # ✅ Normalize candidateType
        candidate_type = payload.candidateType.lower() if payload.candidateType else "experienced"

        prompt = jd_structuring_prompt(
            jd_paragraph=payload.jobDescription,
            experience_input=payload.experience,
            explicit_skills_mustHave=payload.mustHave,
            explicit_skills_goodToHave=payload.goodToHave,
            explicit_certifications=payload.certifications
        )

        try:
            llm_response = await call_llm(prompt)
        except AppError:
            raise
        except Exception as e:
            raise AppError(f"JD structuring LLM failed: {str(e)}", 500)

        try:
            parsed = json.loads(llm_response)
        except json.JSONDecodeError:
            raise AppError("LLM returned invalid JSON", 500)

        experience = parsed.get("experience", {})
        skills = parsed.get("skills", {})
        certifications = parsed.get("certifications", [])

        # ✅ Validation
        if not isinstance(experience, dict):
            raise AppError("Invalid schema: experience must be dict", 400)

        exp_text = experience.get("experienceText")

        if not exp_text:
            raise AppError("Job Description is Required", 400)

        # ✅ Clean skills
        must_have_clean = clean_skill_list(skills.get("mustHave", []))
        good_to_have_clean = clean_skill_list(skills.get("goodToHave", []))

        good_to_have_clean = [
            s for s in good_to_have_clean if s not in must_have_clean
        ]

        # ✅ Final JD document (UPDATED)
        jd_doc = {
            "name": payload.name,
            "experience": experience,
            "mustHave": must_have_clean,
            "goodToHave": good_to_have_clean,
            "jobDescription": payload.jobDescription,
            "certifications": certifications,
            "candidateType": candidate_type   # 🔥 ADDED HERE
        }

        # ✅ Insert into DB
        try:
            result = collection.insert_one(jd_doc)
        except Exception as e:
            raise AppError(f"Database insert failed: {str(e)}", 500)

        # ✅ Response (UPDATED)
        return {
            "response": True,
            "result": {
                "type": "success",
                "data": {
                    "jd_id": str(result.inserted_id),
                    "mustHave": must_have_clean,
                    "goodToHave": good_to_have_clean,
                    "certifications": certifications,
                    "candidateType": candidate_type   # 🔥 RETURNED
                }
            }
        }

    except AppError:
        raise
    except Exception as e:
        raise AppError(f"JD processing failed: {str(e)}", 500)