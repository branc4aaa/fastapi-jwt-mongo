from .routes_auth import app_router as auth_router
from .routes_user import router as user_router
from fastapi import FastAPI

app = FastAPI(title="FastAPI JWT + Mongo Microservice")
app.include_router(auth_router)
app.include_router(user_router)
