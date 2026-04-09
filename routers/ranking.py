from bson import ObjectId
from typing import Any, Dict
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
from database.connection import db
from services.app_error import AppError
from controller.ranking.rank import calculate_resume_score

router = APIRouter()

def serialize_mongo_doc(doc: Any) -> Any:
    if isinstance(doc, list):
        return [serialize_mongo_doc(item) for item in doc]
    if isinstance(doc, dict):
        return {k: serialize_mongo_doc(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc


@router.post("/api/resume_ranking/rank/{job_id}")
async def rank_resumes(job_id: str) -> Dict[str, Any]:

    try:
        if not ObjectId.is_valid(job_id):
            raise AppError("Invalid job_id", 400)

        job_object_id = ObjectId(job_id)

        job = db["jobdescriptions"].find_one({"_id": job_object_id})

        if not job:
            raise AppError("Job not found", 404)

        department = job.get("name")

        if not department:
            raise AppError("JD title missing in job data", 500)

        resumes = list(
            db["candidateprofiles"].find({
                "summaryForAI": {"$exists": True, "$nin": [None, {}]}
            })
        )

        if not resumes:
            response_data = {
                "job_id": job_id,
                "designation": department,
                "total_resumes": 0,
                "ranked_resumes": []
            }

            return {
                "response": True,
                "result": {
                    "type": "success",
                    "data": response_data
                }
            }

        ranked = []

        for resume in resumes:
            try:
                score_data = await calculate_resume_score(resume, job)

                ranked.append({
                    "resume_id": str(resume["_id"]),

                    "name": (
                        resume.get("name") or
                        resume.get("summaryForAI", {}).get("name") or
                        resume.get("fullName") or
                        "Candidate"
                    ),

                    "final_score": round(score_data["final_score"], 4),

                    "skills_score": round(score_data["scores"]["skills"] * 100, 2),
                    "experience_score": round(score_data["scores"]["experience"] * 100, 2),
                    "education_score": round(score_data["scores"]["education"] * 100, 2),
                })

            except Exception as e:
                raise AppError(
                    f"Resume scoring failed for resume {resume['_id']}: {str(e)}",
                    500
                )

        ranked.sort(key=lambda x: x["final_score"], reverse=True)

        for i, item in enumerate(ranked):
            rank_position = i + 1
            resume_id = ObjectId(item["resume_id"])

            db["candidateprofiles"].update_one(
                {"_id": resume_id},
                {
                    "$push": {
                        "rankings": {
                            "rankId": job_object_id,
                            "score": item["final_score"],
                            "rank": rank_position,
                            "rankedAt": datetime.now()
                        }
                    }
                }
            )

        response_data = {
            "job_id": job_id,
            "designation": department,
            "total_resumes": len(ranked),
            "ranked_resumes": [
                {
                    "rank": i + 1,
                    "resume_id": r["resume_id"],
                    "name": r["name"],
                    "final_score": r["final_score"],
                    "skills_score": r["skills_score"],
                    "experience_score": r["experience_score"],
                    "education_score": r["education_score"],
                }
                for i, r in enumerate(ranked)
            ]
        }

        return {
            "response": True,
            "result": {
                "type": "success",
                "data": response_data
            }
        }

    except AppError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "response": False,
                "result": {
                    "type": "error",
                    "data": {}
                },
                "message": e.message
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "response": False,
                "result": {
                    "type": "error",
                    "data": {}
                },
                "message": f"Internal Server Error: {str(e)}"
            }
        )