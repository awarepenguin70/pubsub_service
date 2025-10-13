# models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal, Union
from uuid import UUID, uuid4
from datetime import datetime, timezone

# --- Core & REST Models ---

class CreateTopicRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class TopicStatusResponse(BaseModel):
    status: str
    topic: str

class TopicInfo(BaseModel):
    name: str
    subscribers: int

class ListTopicsResponse(BaseModel):
    topics: List

class HealthResponse(BaseModel):
    uptime_sec: int
    topics: int
    subscribers: int

class TopicStats(BaseModel):
    messages: int
    subscribers: int

class StatsResponse(BaseModel):
    topics: Dict

# --- WebSocket Message Payloads ---

class MessagePayload(BaseModel):
    id: UUID
    payload: Dict[str, Any]

class ErrorPayload(BaseModel):
    code: str
    message: str

# --- Client -> Server WebSocket Messages ---

class ClientSubscribeMessage(BaseModel):
    type: Literal["subscribe"]
    topic: str
    client_id: str
    last_n: Optional[int] = Field(0, ge=0)
    request_id: Optional[str] = None

class ClientUnsubscribeMessage(BaseModel):
    type: Literal["unsubscribe"]
    topic: str
    client_id: str
    request_id: Optional[str] = None

class ClientPublishMessage(BaseModel):
    type: Literal["publish"]
    topic: str
    message: MessagePayload
    request_id: Optional[str] = None

class ClientPingMessage(BaseModel):
    type: Literal["ping"]
    request_id: Optional[str] = None

ClientMessage = Union

# --- Server -> Client WebSocket Messages ---

class ServerAckMessage(BaseModel):
    type: Literal["ack"] = "ack"
    request_id: Optional[str] = None
    topic: Optional[str] = None
    status: str = "ok"
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServerEventMessage(BaseModel):
    type: Literal["event"] = "event"
    topic: str
    message: MessagePayload
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServerErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    request_id: Optional[str] = None
    error: ErrorPayload
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServerPongMessage(BaseModel):
    type: Literal["pong"] = "pong"
    request_id: Optional[str] = None
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServerInfoMessage(BaseModel):
    type: Literal["info"] = "info"
    topic: Optional[str] = None
    msg: str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))