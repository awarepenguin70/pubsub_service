# manager.py
import asyncio
import collections
from typing import Dict, List, Set, Deque
from fastapi import WebSocket, HTTPException
from starlette.websockets import WebSocketState
import models

class Topic:
    """Encapsulates all state for a single topic."""
    def __init__(self, name: str):
        self.name = name
        self.subscribers: Dict[str, WebSocket] = {}
        self.message_history: Deque[models.ServerEventMessage] = collections.deque(maxlen=100)
        self.message_count: int = 0

    async def broadcast(self, message: models.ServerEventMessage):
        """Sends a message to all subscribers of this topic."""
        disconnected_clients: List[str] = []
        for client_id, websocket in list(self.subscribers.items()):
            # use getattr to avoid attribute errors on different WebSocket implementations
            if getattr(websocket, "client_state", None) == WebSocketState.CONNECTED:
                await websocket.send_json(message.dict())
            else:
                disconnected_clients.append(client_id)

        # Clean up any disconnected clients found during broadcast
        for client_id in disconnected_clients:
            del self.subscribers[client_id]


# manager.py
# (Add these methods to the existing PubSubManager class)

class PubSubManager:
    #... (existing methods from Phase 2)...




    def __init__(self):
        self._topics: Dict[str, Topic] = {}
        self._clients: Dict[str, Set[str]] = {}  # client_id -> set of subscribed topics
        self.lock = asyncio.Lock()

    async def create_topic(self, name: str):
        async with self.lock:
            if name in self._topics:
                raise HTTPException(status_code=409, detail="Topic already exists")
            self._topics[name] = Topic(name=name)

    async def delete_topic(self, name: str):
        async with self.lock:
            if name not in self._topics:
                raise HTTPException(status_code=404, detail="Topic not found")

            topic = self._topics[name]
            info_message = models.ServerInfoMessage(topic=name, msg="topic_deleted")

            # Notify and disconnect all subscribers of this topic
            for client_id, websocket in list(topic.subscribers.items()):
                if getattr(websocket, "client_state", None) == WebSocketState.CONNECTED:
                    await websocket.send_json(info_message.dict())
                    await websocket.close(code=1000)

                # Clean up client's subscription list
                if client_id in self._clients:
                    self._clients[client_id].discard(name)
                    if not self._clients[client_id]:
                        del self._clients[client_id]

            del self._topics[name]

    async def list_topics(self) -> List[str]:
        async with self.lock:
            return list(self._topics.keys())

    async def get_health_stats(self) -> models.HealthResponse:
        async with self.lock:
            total_subscribers = sum(len(topic.subscribers) for topic in self._topics.values())
            return models.HealthResponse(
                uptime_sec=0, # Will be calculated in the endpoint
                topics=len(self._topics),
                subscribers=total_subscribers
            )

    async def get_full_stats(self) -> models.StatsResponse:
        async with self.lock:
            topic_stats = {
                name: models.TopicStats(
                    messages=topic.message_count,
                    subscribers=len(topic.subscribers)
                )
                for name, topic in self._topics.items()
            }
            return models.StatsResponse(topics=topic_stats)


    async def subscribe(self, topic_name: str, client_id: str, websocket: WebSocket, last_n: int):
        async with self.lock:
            if topic_name not in self._topics:
                raise ValueError("TOPIC_NOT_FOUND")

            topic = self._topics[topic_name]
            topic.subscribers[client_id] = websocket

            if client_id not in self._clients:
                self._clients[client_id] = set()
            self._clients[client_id].add(topic_name)

            # Handle message replay for last_n
            if last_n > 0:
                history = list(topic.message_history)
                replay_messages = history[-last_n:]
                for msg_payload in replay_messages:
                    event = models.ServerEventMessage(topic=topic_name, message=msg_payload)
                    await websocket.send_json(event.dict())

    async def unsubscribe(self, topic_name: str, client_id: str):
        async with self.lock:
            if topic_name not in self._topics:
                raise ValueError("TOPIC_NOT_FOUND")

            topic = self._topics[topic_name]
            if client_id in topic.subscribers:
                del topic.subscribers[client_id]

            if client_id in self._clients:
                self._clients[client_id].discard(topic_name)
                if not self._clients[client_id]:
                    del self._clients[client_id]

    async def publish(self, topic_name: str, message: models.MessagePayload):
        async with self.lock:
            if topic_name not in self._topics:
                raise ValueError("TOPIC_NOT_FOUND")

            topic = self._topics[topic_name]
            topic.message_history.append(message)
            topic.message_count += 1

            event = models.ServerEventMessage(topic=topic_name, message=message)
            await topic.broadcast(event)

    async def disconnect_client(self, client_id: str):
        async with self.lock:
            if client_id in self._clients:
                topics_to_unsubscribe = list(self._clients[client_id])
                for topic_name in topics_to_unsubscribe:
                    if topic_name in self._topics:
                        topic = self._topics[topic_name]
                        if client_id in topic.subscribers:
                            del topic.subscribers[client_id]
                del self._clients[client_id]