from fastapi import FastAPI

from users_import import router as users_import_router

app = FastAPI(title="JSON2Mongo API")

app.include_router(users_import_router)