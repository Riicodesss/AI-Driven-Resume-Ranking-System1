import os, re, json, asyncio, requests, base64, fitz
from io import BytesIO
from PIL import Image
from docx import Document
from dotenv import load_dotenv
from pymongo import MongoClient, ReadPreference
from ollama import AsyncClient

from utils.summaryforai import SYSTEM_PROMPT_SUMMARY_FOR_AI

load_dotenv()

MODEL = os.getenv("RESUME_MODEL")
DB_URL = os.getenv("CONNECTION_STRING")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

client = MongoClient(DB_URL, read_preference=ReadPreference.PRIMARY)
db = client["resume_ranking"]
collection = db["candidateprofiles"]

ollama = AsyncClient(host=OLLAMA_HOST)


def sanitize_resume_url(raw_url: str):
    if not raw_url:
        return None
    match = re.search(r"(https?://[^\s]+)", raw_url)
    return match.group(1) if match else None


def fetch_file_bytes(url: str) -> bytes:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def detect_file_type(file_bytes: bytes):
    if file_bytes[:4] == b"%PDF":
        return "pdf"
    if file_bytes[:2] == b"PK":
        return "docx"
    return None


def pdf_to_image(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    page = doc.load_page(0)
    pix = page.get_pixmap()
    return Image.open(BytesIO(pix.tobytes("png")))


def image_to_base64(img):
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


async def extract_text_from_resume(file_bytes, file_type):
    if file_type == "docx":
        doc = Document(BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    if file_type == "pdf":
        with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
            text = ""
            for page in pdf:
                text += page.get_text()

            clean = re.sub(r"\W", "", text)

            if len(clean) < 100:
                img = pdf_to_image(file_bytes)
                img_b64 = image_to_base64(img)

                response = await ollama.chat(
                    model="qwen3-vl:235b-instruct-cloud",
                    messages=[{
                        "role": "user",
                        "content": "Extract all text",
                        "images": [img_b64]
                    }]
                )
                return response["message"]["content"]

            return text

    return ""

async def generate_summary_for_ai(resume_text: str):
    try:
        response = await ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_SUMMARY_FOR_AI  
                },
                {
                    "role": "user",
                    "content": resume_text 
                }
            ]
        )

        raw = response["message"]["content"]

        return json.loads(raw)

    except Exception as e:
        raise Exception(f"LLM failed: {e}")


async def process_candidate(candidate_id: str):
    try:
        candidate = collection.find_one({"_id": candidate_id})

        if not candidate:
            print("Candidate not found")
            return

        url = sanitize_resume_url(candidate.get("uploadResume"))

        if not url:
            print("Invalid resume URL")
            return

        file_bytes = fetch_file_bytes(url)

        file_type = detect_file_type(file_bytes)

        if not file_type:
            print("Unsupported file type")
            return

        print(f"📄 Detected: {file_type}")

        resume_text = await extract_text_from_resume(file_bytes, file_type)

        if not resume_text.strip():
            print("Empty resume text")
            return

        summary_ai_data = await generate_summary_for_ai(resume_text)

        summary_for_ai = summary_ai_data.get("summaryforai", {})

        collection.update_one(
            {"_id": candidate_id},
            {
                "$set": {
                    "summaryForAI": summary_for_ai,
                    "isProcessed": True
                }
            }
        )

        print(f"✅ Processed candidate: {candidate_id}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def watch_candidates():
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"operationType": "insert"},
                    {"updateDescription.updatedFields.uploadResume": {"$exists": True}}
                ]
            }
        }
    ]

    with collection.watch(pipeline) as stream:
        for change in stream:
            cid = change["documentKey"]["_id"]
            await process_candidate(cid)


if __name__ == "__main__":
    print("🚀 Watching candidate uploads...")
    asyncio.run(watch_candidates())