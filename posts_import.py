import httpx
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pymongo.errors import DuplicateKeyError, PyMongoError, WriteError

from jsonplaceholder_client import get_posts
from mongo_collections import posts_collection, users_collection


router = APIRouter(prefix="/import", tags=["Import"])


def users_exist() -> bool:
    return users_collection.find_one({}, {"_id": 1}) is not None


def import_posts_to_mongo(posts: list[dict]) -> dict:
    inserted = 0
    skipped = 0
    failed = 0

    for post in posts:
        source_id = post.get("id")
        source_user_id = post.get("userId")
        if source_id is None or source_user_id is None:
            failed += 1
            continue

        user = users_collection.find_one({"source_id": source_user_id}, {"_id": 1})
        if user is None:
            failed += 1
            continue

        try:
            if posts_collection.find_one({"source_id": source_id}, {"_id": 1}):
                skipped += 1
                continue

            document = {k: v for k, v in post.items() if k not in ("id", "userId")}
            document["source_id"] = source_id
            document["source_user_id"] = source_user_id
            document["user_id"] = user["_id"]
            posts_collection.insert_one(document)
            inserted += 1
        except DuplicateKeyError:
            skipped += 1
        except WriteError:
            failed += 1

    return {
        "fetched": len(posts),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
    }


@router.post("/posts")
async def import_posts():
    try:
        has_users = await run_in_threadpool(users_exist)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {exc}")

    if not has_users:
        raise HTTPException(
            status_code=409,
            detail="No users found. Import users first using POST /import/users.",
        )

    try:
        posts = await get_posts()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JSONPlaceholder returned {exc.response.status_code} for {exc.request.url}",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        return await run_in_threadpool(import_posts_to_mongo, posts)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {exc}")