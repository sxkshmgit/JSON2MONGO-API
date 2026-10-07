import httpx

BASE_URL = "https://jsonplaceholder.typicode.com"
TIMEOUT = httpx.Timeout(10.0)


async def _get(path: str) -> list[dict]:
    url = f"{BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        raise RuntimeError(
            f"Request to {exc.request.url} failed: {type(exc).__name__}: {exc}"
        ) from exc


async def get_users() -> list[dict]:
    return await _get("/users")


async def get_posts() -> list[dict]:
    return await _get("/posts")


async def get_comments() -> list[dict]:
    return await _get("/comments")