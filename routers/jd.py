from typing import Dict, Any
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from bson import ObjectId

from database.connection import db
from services.app_error import AppError
from model.JD_schema import JDInput
from controller.summary.jd_service import process_jd

router = APIRouter(prefix="/api/jd", tags=["Job Description"])

@router.post("/", status_code=status.HTTP_200_OK)
async def create_jd(payload: JDInput) -> Dict[str, Any]:
    try:
        result = await process_jd(payload)

        return {
            "success": True,
            "data": result,
            "message": "JD created successfully"
        }

    except AppError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"success": False, "message": e.message}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

@router.get("/", status_code=status.HTTP_200_OK)
def get_all_jds() -> Dict[str, Any]:
    try:
        jds = list(
            db["jobdescriptions"].find({}, {"name": 1})
        )

        return {
            "success": True,
            "data": [
                {
                    "id": str(jd["_id"]),
                    "name": jd.get("name", "Untitled JD")
                }
                for jd in jds
            ]
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )

        