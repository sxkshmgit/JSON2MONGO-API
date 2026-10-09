from fastapi import FastAPI

from users_import import router as users_import_router
from posts_import import router as posts_import_router
app = FastAPI(title="JSON2Mongo API")

app.include_router(users_import_router)
app.include_router(posts_import_router)