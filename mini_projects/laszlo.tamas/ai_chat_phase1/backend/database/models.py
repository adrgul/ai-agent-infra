from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class User(BaseModel):
    user_id: int
    firstname: str
    lastname: str
    nickname: str
    email: str
    role: str
    is_active: bool
    default_lang: str
    created_at: str


class ChatSession(BaseModel):
    id: str
    user_id: int
    created_at: str


class ChatMessage(BaseModel):
    message_id: Optional[int] = None
    session_id: str
    user_id: int
    role: str
    content: str
    created_at: Optional[str] = None
