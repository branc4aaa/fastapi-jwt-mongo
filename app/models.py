from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: str
    name: Optional[str] = None
    email: EmailStr
