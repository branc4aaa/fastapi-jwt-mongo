from .auth import create_access_token, verify_password, hash_password, create_refresh_token, verify_token
from .schemas import RegisterSchema, LoginSchema, RefreshSchema
from bson import ObjectId
from .db import users_collection
from dotenv import load_dotenv
import os
from jwt import ExpiredSignatureError, InvalidTokenError
import jwt


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

@app_router.post("/refresh")
async def refresh_token(data: RefreshSchema):
    re_token = data.refresh_token 
    try:
        decoded = jwt.decode(re_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")

        user_id = decoded["user_id"]

        user = await users_collection.find_one({"_id": ObjectId(user_id)})

        if not user or user.get("refresh_token") != re_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access = create_access_token({"user_id": user_id})

        return {"access_token": new_access}

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")

    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
