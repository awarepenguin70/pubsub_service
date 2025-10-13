# main.py
import time
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from starlette.responses import JSONResponse
from pydantic import ValidationError

from manager import PubSubManager
import models

app = FastAPI()
start_time = time.time()
manager = PubSubManager()

# --- REST Endpoints ---

@app.post("/topics", status_code=status.HTTP_201_CREATED)
async def create_topic(request: models.CreateTopicRequest) -> models.TopicStatusResponse:
    await manager.create_topic(request.name)
    return models.TopicStatusResponse(status="created", topic=request.name)

@app.delete("/topics/{name}", status_code=status.HTTP_200_OK)
async def delete_topic(name: str) -> models.TopicStatusResponse:
    await manager.delete_topic(name)
    return models.TopicStatusResponse(status="deleted", topic=name)

@app.get("/topics", status_code=status.HTTP_200_OK)
async def list_topics() -> models.ListTopicsResponse:
    topics_list = await manager.list_topics()
    return models.ListTopicsResponse(topics=topics_list)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> models.HealthResponse:
    stats = await manager.get_health_stats()
    stats.uptime_sec = int(time.time() - start_time)
    return stats

@app.get("/stats", status_code=status.HTTP_200_OK)
async def get_stats() -> models.StatsResponse:
    return await manager.get_full_stats()

# --- WebSocket Endpoint (placeholder for now) ---
# main.py
# (Replace the old @app.websocket("/ws") with this new version)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id: Optional[str] = None
    try:
        while True:
            data = await websocket.receive_json()

            try:
                msg_type = data.get("type")
                request_id = data.get("request_id")

                if msg_type == "subscribe":
                    msg = models.ClientSubscribeMessage(**data)
                    client_id = msg.client_id # Associate client_id with this connection
                    await manager.subscribe(msg.topic, msg.client_id, websocket, msg.last_n)
                    ack = models.ServerAckMessage(request_id=request_id, topic=msg.topic)
                    await websocket.send_json(ack.dict())

                elif msg_type == "unsubscribe":
                    msg = models.ClientUnsubscribeMessage(**data)
                    await manager.unsubscribe(msg.topic, msg.client_id)
                    ack = models.ServerAckMessage(request_id=request_id, topic=msg.topic)
                    await websocket.send_json(ack.dict())

                elif msg_type == "publish":
                    msg = models.ClientPublishMessage(**data)
                    await manager.publish(msg.topic, msg.message)
                    ack = models.ServerAckMessage(request_id=request_id, topic=msg.topic)
                    await websocket.send_json(ack.dict())

                elif msg_type == "ping":
                    msg = models.ClientPingMessage(**data)
                    pong = models.ServerPongMessage(request_id=request_id)
                    await websocket.send_json(pong.dict())

                else:
                    raise ValueError("Unsupported message type")

            except ValidationError as e:
                error_payload = models.ErrorPayload(code="BAD_REQUEST", message=str(e))
                error_msg = models.ServerErrorMessage(request_id=request_id, error=error_payload)
                await websocket.send_json(error_msg.dict())

            except ValueError as e:
                error_payload = models.ErrorPayload(code=str(e), message="Operation failed")
                error_msg = models.ServerErrorMessage(request_id=request_id, error=error_payload)
                await websocket.send_json(error_msg.dict())

    except WebSocketDisconnect:
        print(f"Client '{client_id}' disconnected.")

    finally:
        if client_id:
            await manager.disconnect_client(client_id)