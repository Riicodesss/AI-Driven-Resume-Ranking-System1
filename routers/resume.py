from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from database.connection import db

from services.extraction import extract_text_from_pdf
from controller.summary.resume_summary import generate_summary_for_ai

router = APIRouter(prefix="/api/resume", tags=["Resume"])

collection = db["candidateprofiles"]


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    try:
        text = extract_text_from_pdf(file)

        if not text:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Failed to extract text"}
            )

        summary_ai_data = await generate_summary_for_ai(text)

        print("SUMMARY AI DATA:", summary_ai_data)

        summary_for_ai = (
            summary_ai_data.get("summaryforai")
            if isinstance(summary_ai_data, dict)
            else {}
        )

        result = collection.insert_one({
            "file_name": file.filename,
            "resume_text": text,
            "summaryForAI": summary_for_ai
        })

        return {
            "success": True,
            "data": {
                "candidate_id": str(result.inserted_id),
                "summary_preview": summary_for_ai
            },
            "message": "Resume processed and saved successfully"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": str(e)}
        )