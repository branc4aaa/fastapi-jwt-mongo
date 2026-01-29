from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import verify_token
from .db import users_collection
from .schemas import UserResponse
from bson import ObjectId
from bson.errors import InvalidId


router = APIRouter(prefix="", tags=["User"])

security = HTTPBearer()

async def token_v(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    print("RAW:", credentials.scheme, credentials.credentials)
    token = credentials.credentials  
    decoded = verify_token(token, "access")

    if not decoded:
        raise HTTPException(status_code=401, detail="Token invalid or expired")
    return decoded

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
#@router.post("/test-token/{user_id}")
#async def test_token( user_id:str, data, token = Depends(token_v)):
#    
#    data = await users_collection.find_one({"_id": ObjectId(user_id)})
#    if not data:
#        raise HTTPException(status_code=404, detail="User not found")
#    data["_id"] = str(data["_id"])
#    return {"message": "Token is valid", "user": data}
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

