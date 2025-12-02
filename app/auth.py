import os
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from fastapi import HTTPException
from datetime import datetime, timedelta
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES"))

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# Hash password
def hash_password(password: str):
    return pwd_context.hash(password)

# Verify password
def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

# JWT creation
def create_access_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
    if payload["exp"] > datetime.utcnow() - timedelta(minutes=JWT_EXPIRES_MINUTES):
        payload["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXPIRES_MINUTES)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# JWT verification
def verify_token(token: str):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )