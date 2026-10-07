from pymongo import ASCENDING

from database import db

users_collection = db["users"]
posts_collection = db["posts"]
comments_collection = db["comments"]

users_collection.create_index([("source_id", ASCENDING)], unique=True)
posts_collection.create_index([("source_id", ASCENDING)], unique=True)
comments_collection.create_index([("source_id", ASCENDING)], unique=True)