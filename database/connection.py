import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

DB_URL = "mongodb://127.0.0.1:27017"

try:
    client = MongoClient(DB_URL, serverSelectionTimeoutMS=5000)

    client.server_info()

    db = client["resume_ranking"]

    print("✅ Connected to LOCAL MongoDB")

except Exception as e:
    print("❌ Failed to connect to LOCAL MongoDB")
    print(e)
    raise e


def get_db():
    return db