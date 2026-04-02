import os, re
from ollama import AsyncClient
from services.app_error import AppError

OLLAMA_HOST = os.getenv("OLLAMA_HOST")
ollama = AsyncClient(host=OLLAMA_HOST)

MODEL = os.getenv("RESUME_MODEL")

async def call_llm(prompt: str) -> str:

    if not MODEL:
        raise AppError("RESUME_MODEL environment variable is not configured", 500)

    try:
        response = await ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a JD parsing and structuring expert."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0,
                "num_ctx": 8192
            }
        )
    except Exception as e:
        raise AppError(f"Ollama LLM call failed: {str(e)}", 400)

    raw_output = response["message"]["content"].strip()
    raw_output = raw_output.replace("```json", "").replace("```", "").strip()

    if not raw_output:
        raise AppError("LLM returned empty response", 500)

    return raw_output

def clean_skill_list(items):

    if not isinstance(items, list):
        return []

    cleaned = []
    seen = set()

    for item in items:

        if not item:
            continue

        item = str(item).strip().lower()
        item = re.sub(r"\s+", " ", item)

        if len(item) < 2:
            continue

        if item.isdigit():
            continue

        if not re.search(r"[a-zA-Z]", item):
            continue

        if item not in seen:
            seen.add(item)
            cleaned.append(item)

    return cleaned