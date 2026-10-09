import httpx
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pymongo.errors import DuplicateKeyError, PyMongoError, WriteError

from jsonplaceholder_client import get_comments
from mongo_collections import comments_collection, posts_collection

router = APIRouter(prefix="/import", tags=["Import"])


def posts_exist() -> bool:
    return posts_collection.find_one({}, {"_id": 1}) is not None


def import_comments_to_mongo(comments: list[dict]) -> dict:
    inserted = 0
    skipped = 0
    failed = 0

    for comment in comments:
        source_id = comment.get("id")
        source_post_id = comment.get("postId")
        if source_id is None or source_post_id is None:
            failed += 1
            continue

        post = posts_collection.find_one({"source_id": source_post_id}, {"_id": 1})
        if post is None:
            failed += 1
            continue

        try:
            if comments_collection.find_one({"source_id": source_id}, {"_id": 1}):
                skipped += 1
                continue

            document = {k: v for k, v in comment.items() if k not in ("id", "postId")}
            document["source_id"] = source_id
            document["source_post_id"] = source_post_id
            document["post_id"] = post["_id"]
            comments_collection.insert_one(document)
            inserted += 1
        except DuplicateKeyError:
            skipped += 1
        except WriteError:
            failed += 1

    return {
        "fetched": len(comments),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
    }


@router.post("/comments")
async def import_comments():
    try:
        has_posts = await run_in_threadpool(posts_exist)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {exc}")

    if not has_posts:
        raise HTTPException(
            status_code=409,
            detail="No posts found. Import posts first using POST /import/posts.",
        )

    try:
        comments = await get_comments()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JSONPlaceholder returned {exc.response.status_code} for {exc.request.url}",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        return await run_in_threadpool(import_comments_to_mongo, comments)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {exc}")