from .auth import create_access_token, verify_password, hash_password
from .schemas import RegisterSchema, LoginSchema
from bson import ObjectId
from .db import users_collection
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os


from fastapi import HTTPException,  APIRouter, status

app_router = APIRouter(prefix="/auth", tags=["Auth"])

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES"))


@app_router.post("/register")
async def register(user: RegisterSchema):
    searchUser = await users_collection.find_one({"email": user.email})
    if searchUser:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email already registered")
    hp = hash_password(user.password)
    nu = {
        "name": user.name,
        "email": user.email,
        "password": hp
    }
    newU = await users_collection.insert_one(nu)
    return {"id": str(newU.inserted_id), "name": user.name, "email": user.email}

@app_router.post("/login")
async def login(user: LoginSchema):
    su = await users_collection.find_one({"email": user.email})
    if not su:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )   
    if not verify_password(user.password, su["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )
    token = create_access_token({"user_id": str(su["_id"]), "email": su["email"]})
    ans = {"access_token": token, "token_type": "bearer"}
    texp = ans.get("access_token")
    if texp["exp"]> datetime.utcnow() - timedelta(minutes=JWT_EXPIRES_MINUTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expired login again")

    return 