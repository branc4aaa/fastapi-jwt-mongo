from .auth import create_access_token, verify_password, hash_password, create_refresh_token, verify_token
from .schemas import RegisterSchema, LoginSchema, RefreshSchema
from bson import ObjectId
from .db import users_collection
from dotenv import load_dotenv
import os

from fastapi import HTTPException,  APIRouter, status

app_router = APIRouter(prefix="/auth", tags=["Auth"])

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES"))

#User signup
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

#User login
@app_router.post("/login")
async def login(user: LoginSchema):
    su = await users_collection.find_one({"email": user.email})
    if not su or not verify_password(user.password, su["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )   
    
    access = create_access_token({"user_id": str(su["_id"])})
    refresh = create_refresh_token({"user_id": str(su["_id"])})
    await users_collection.update_one(
        {"_id": su["_id"]},
        {"$set": {"refresh_token": refresh}}
    )
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer"
    }

#Token refresh
@app_router.post("/refresh")
async def refresh(data: RefreshSchema):

    decoded = verify_token(data.refresh_token, "refresh")

    user_id = decoded.get("user_id")

    user = await users_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(404, "User not found")
    if user.get("refresh_token") != data.refresh_token:
        raise HTTPException(401, "Invalid refresh token")

    new_access = create_access_token({
        "user_id": user_id,
        "email": user["email"]
    })

    return {
        "access_token": new_access,
        "token_type": "bearer"
    }

