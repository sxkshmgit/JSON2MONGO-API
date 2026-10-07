import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is not set. Add it to your .env file.")

client = MongoClient(MONGODB_URI)
db = client["json2mongo"]


def ping_database() -> bool:
    client.admin.command("ping")
    return True


if __name__ == "__main__":
    ping_database()
    print("Successfully connected to MongoDB.")