from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()

from routers.jd import router as jd_router
from routers.resume import router as resume_router
import routers.ranking as ranking_router 

app = FastAPI(
    title="Resume Ranking API",
    description="AI-powered system to analyze job descriptions and rank candidates",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jd_router)
app.include_router(resume_router)
app.include_router(ranking_router.router)

@app.get("/")
def root():
    return {
        "message": "Resume Ranking API is running 🚀",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)