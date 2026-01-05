from pydantic import BaseModel


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
