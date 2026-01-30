from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import verify_token
from .db import users_collection
from .schemas import UserResponse, UpdateUserSchema
from bson import ObjectId
from bson.errors import InvalidId


router = APIRouter(prefix="", tags=["User"])

security = HTTPBearer()

async def token_v(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    
    token = credentials.credentials  
    decoded = verify_token(token, "access")

    if not decoded:
        raise HTTPException(status_code=401, detail="Token invalid or expired")
    return decoded

# get user by id
@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, token: dict = Depends(token_v)):
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(400, "Invalid user id")

    user = await users_collection.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
    )

#get all users
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

    if not users:
        raise HTTPException(status_code=404, detail="No users found")

    return users 

#test token validity
@router.post("/test-token/{user_id}")
async def test_token(user_id: str,sec=Depends(token_v)):

    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(400, "Invalid user id")

    user = await users_collection.find_one({"_id": oid})

    if not user:
        raise HTTPException(404, "User not found")

    user["_id"] = str(user["_id"])

    return {"message": "Token is valid","user": user}

#put user
@router.put("/user/{user_id}")
async def update_user(user_id: str, data:UpdateUserSchema, token = Depends(token_v)):

    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(400, "Invalid user id")

    user = await users_collection.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    existing_user = await users_collection.find_one(
        {"email": data.email, "_id": {"$ne": oid}}
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already in use"
        )

    await users_collection.update_one(
        {"_id": oid},
        {"$set": {
            "name": data.name,
            "email": data.email
        }}
    )

    return {"message": "User updated successfully"}

#delete user
@router.delete("/user/{user_id}")
async def delete_user(user_id: str, token = Depends(token_v)):

    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(400, "Invalid user id")

    user = await users_collection.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await users_collection.delete_one({"_id": oid})
    return {"message": "User deleted successfully"}

