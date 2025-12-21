from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: int = Field(..., description="ID of the user sending the message")
    session_id: str = Field(..., description="UUID of the chat session")
    message: str = Field(..., description="User's message content")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Assistant's response")


class MessageResponse(BaseModel):
    message_id: int
    session_id: str
    user_id: int
    role: str
    content: str
    created_at: str


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
