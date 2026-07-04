from pydantic import BaseModel
from typing import Optional, List


class GeneratePlanRequest(BaseModel):
    week_number: Optional[int] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    reply: str


class WeeklyReviewRequest(BaseModel):
    week_number: Optional[int] = None
