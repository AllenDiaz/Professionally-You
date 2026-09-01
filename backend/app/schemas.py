"""Pydantic request/response models for the API."""

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str


class HealthResponse(BaseModel):
    status: str
    vertex_configured: bool
    pushover_configured: bool
    model: str
