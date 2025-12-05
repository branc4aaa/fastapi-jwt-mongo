from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from .auth import verify_token
from .db import users_collection
from .schemas import UserResponse
from bson import ObjectId

from dotenv import load_dotenv
import os

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES"))


router = APIRouter(prefix="", tags=["User"])

security = HTTPBearer()

async def token_v(token:str = Depends(security)):
    decoded = verify_token(token.credentials)
    if not decoded:
        raise HTTPException(status_code=401, detail="Token invalid or expired")
    return decoded

@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, token: dict = Depends(token_v)):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
    )
@router.get("/users")
async def get_users():

    users_cursor = users_collection.find()
    users = []

    async for u in users_cursor:
        users.append({
            "id": str(u["_id"]),
            "name": u.get("name"),
            "email": u.get("email"),
            "token": u.get("refresh_token"),
            "token2": u.get("access_token")
        })

    return users
@router.get("/test-token")
def test_token(token: dict = Depends(token_v)):
    return {"message": "Token is valid", "token_data": token}