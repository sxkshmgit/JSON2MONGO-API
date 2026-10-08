import httpx
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pymongo.errors import DuplicateKeyError, PyMongoError, WriteError

from jsonplaceholder_client import get_users
from mongo_collections import users_collection

router = APIRouter(prefix="/import", tags=["Import"])


def import_users_to_mongo(users: list[dict]) -> dict:
    inserted = 0
    skipped = 0
    failed = 0

    for user in users:
        source_id = user.get("id")
        if source_id is None:
            failed += 1
            continue

        try:
            if users_collection.find_one({"source_id": source_id}, {"_id": 1}):
                skipped += 1
                continue

            document = {k: v for k, v in user.items() if k != "id"}
            document["source_id"] = source_id
            users_collection.insert_one(document)
            inserted += 1
        except DuplicateKeyError:
            skipped += 1
        except WriteError:
            failed += 1

    return {
        "fetched": len(users),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed,
    }


@router.post("/users")
async def import_users():
    try:
        users = await get_users()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JSONPlaceholder returned {exc.response.status_code} for {exc.request.url}",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        return await run_in_threadpool(import_users_to_mongo, users)
    except PyMongoError as exc:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {exc}")