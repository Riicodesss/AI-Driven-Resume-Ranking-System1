from model.weights import get_scoring_weights
from controller.ranking.education import education_score
from controller.ranking.skills_llm import llm_match_resume_skills
from controller.ranking.skills import final_skill_score_from_counts
from controller.ranking.experience_llm import get_relevant_experiences
from controller.ranking.experience import final_experience_score
from services.app_error import AppError


def resolve_candidate_level(job: dict) -> str:
    jd_candidate_type = job.get("candidateType")

    if jd_candidate_type:
        return jd_candidate_type.lower()

    return "experienced"

async def calculate_resume_score(resume: dict, job: dict) -> dict:
    """
    Calculate the overall resume score (skills + education + experience).
    """
    try:
        level = resolve_candidate_level(job)

        try:
            llm_result = await llm_match_resume_skills(
                job=job,
                resume=resume
            )
        except AppError:
            raise
        except Exception as e:
            raise AppError(f"Skill LLM matching failed: {str(e)}", 500)

        must_have = job.get("mustHave") or []
        good_to_have = job.get("goodToHave") or []

        skill_result = final_skill_score_from_counts(
            matched_must_have=llm_result["matched_must_have"],
            matched_good_to_have=llm_result["matched_good_to_have"],
            total_must_have=len(must_have),
            total_good_to_have=len(good_to_have)
        )

        resume_ai = resume.get("summaryForAI") or resume

        edu = education_score(
            resume_ai.get("education", []),
            candidate_type=level
        )

        try:
            relevant_data = await get_relevant_experiences(resume, job)
        except AppError:
            raise
        except Exception as e:
            raise AppError(f"Experience relevance extraction failed: {str(e)}", 500)

        exp_result = final_experience_score(
            relevant_data,
            job
        )

        try:
            weights = get_scoring_weights(level)
        except Exception as e:
            raise AppError(f"Failed to load scoring weights: {str(e)}", 500)

        total_weight = (
            weights["skills"] +
            weights["education"] +
            weights["experience"]
        )

        if total_weight == 0:
            raise AppError("Invalid scoring weights: total weight is zero", 500)

        final_score = round(
            (
                weights["skills"] * skill_result["final_skill_score"] +
                weights["education"] * edu["score"] +
                weights["experience"] * exp_result["score"]
            ) / total_weight,
            4
        )
        
        return {
            "candidate_level": level,
            "final_score": final_score,
            "scores": {
                "skills": skill_result["final_skill_score"],
                "education": edu["score"],
                "experience": exp_result["score"]
            },
            "weights_used": {
                "skills": weights["skills"],
                "education": weights["education"],
                "experience": weights["experience"]
            },
            "breakdown": {
                "skills": skill_result,
                "education": edu,
                "experience": exp_result
            }
        }

    except AppError as e:
        raise e
    except Exception as e:
        raise AppError(f"Resume scoring failed: {str(e)}", 500)
    
