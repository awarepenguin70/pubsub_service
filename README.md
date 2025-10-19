# In-Memory Pub/Sub System

A lightweight, real-time Publish/Subscribe messaging system built with FastAPI and WebSockets. Designed for simplicity and ease of deployment with no external dependencies.

## Features

### Core Functionality
- **Real-Time Messaging**: WebSocket-based pub/sub with instant message delivery
- **Topic Management**: Create, delete, and list topics via REST API
- **Message Replay**: Automatically replays last 100 messages to new subscribers
- **Multi-Subscriber Support**: Multiple clients can subscribe to the same topic simultaneously
- **Concurrency Safe**: Thread-safe operations using asyncio locks

### System Capabilities
- **System Observability**: Health checks and statistics endpoints for monitoring
- **In-Memory Storage**: Zero configuration - no database or message broker required
- **WebSocket Protocol**: Supports subscribe, unsubscribe, publish, and ping actions
- **Backpressure Handling**: Built-in flow control for slow consumers

## Project Structure

```
pubsub_service/
├── main.py              # FastAPI application with pub/sub logic
├── manager.py           # Topic and subscriber management
├── models.py            # Pydantic models for API validation
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker container configuration
├── .dockerignore        # Docker build exclusions
└── README.md           # This file
```

## API Reference

### REST Endpoints

#### Create Topic
```http
POST /topics
Content-Type: application/json

{
  "name": "my-topic"
}
```

**Response**: `201 Created`

#### Delete Topic
```http
DELETE /topics/{topic_name}
```

**Response**: `200 OK` - Disconnects all subscribers and removes the topic

#### List Topics
```http
GET /topics
```

**Response**:
```json
{
  "topics": [
    {
      "name": "my-topic",
      "subscriber_count": 3
    }
  ]
}
```

#### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600
}
```

#### Statistics
```http
GET /stats
```

**Response**:
```json
{
  "topics": {
    "my-topic": {
      "subscribers": 3,
      "messages_published": 150,
      "messages_in_history": 100
    }
  }
}
```

### WebSocket Endpoint

Connect to: `ws://localhost:8000/ws`

#### Subscribe to Topic
```json
{
  "action": "subscribe",
  "topic": "my-topic",
  "replay_last": 10
}
```

**Response**: Receives last 10 messages (if available) and all new messages

#### Unsubscribe from Topic
```json
{
  "action": "unsubscribe",
  "topic": "my-topic"
}
```

#### Publish Message
```json
{
  "action": "publish",
  "topic": "my-topic",
  "message": {
    "data": "Hello, World!",
    "timestamp": "2025-01-01T12:00:00Z"
  }
}
```

#### Ping (Keep-Alive)
```json
{
  "action": "ping"
}
```

**Response**:
```json
{
  "action": "pong"
}
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip package manager
- (Optional) Docker for containerized deployment

### Local Development

1. **Clone the repository**:

```bash
git clone https://github.com/awarepenguin70/pubsub_service.git
cd pubsub_service
```

2. **Create and activate a virtual environment**:

```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

The `requirements.txt` should contain:

```
fastapi
uvicorn[standard]
websockets
pydantic
```

4. **Run the application**:

```bash
uvicorn main:app --reload
```

The service will be available at `http://127.0.0.1:8000`

## Usage Examples

### Python Client Example

```python
import asyncio
import websockets
import json

async def pubsub_client():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        # Subscribe to a topic
        await websocket.send(json.dumps({
            "action": "subscribe",
            "topic": "news",
            "replay_last": 5
        }))
        
        # Receive messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(pubsub_client())
```

### JavaScript Client Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    // Subscribe to topic
    ws.send(JSON.stringify({
        action: 'subscribe',
        topic: 'news',
        replay_last: 5
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Publish a message
ws.send(JSON.stringify({
    action: 'publish',
    topic: 'news',
    message: { text: 'Breaking news!' }
}));
```

### cURL Examples

**Create a topic**:
```bash
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"name": "events"}'
```

**List all topics**:
```bash
curl http://localhost:8000/topics
```

**Get system stats**:
```bash
curl http://localhost:8000/stats
```

## Design Decisions & Architecture

### Concurrency Model

The system uses a single global `asyncio.Lock` to serialize access to shared state (topics, subscribers, message history).

**Advantages**:
- Guarantees correctness and prevents race conditions
- Simple to implement and reason about
- Fast development under time constraints

**Trade-offs**:
- ⚠️ May become a bottleneck under extremely high load
- ⚠️ Could be optimized with per-topic locks for better parallelism

### Message History & Replay

- Each topic maintains a `collections.deque` with `maxlen=100`
- Provides an efficient ring buffer for the "replay last N messages" feature
- Only the most recent 100 messages are stored per topic
- History size is currently hardcoded (not configurable)

### In-Memory Storage

**Advantages**:
- Extremely fast - no disk I/O
- Zero configuration - no database setup
- Lightweight deployment

**Limitations**:
- Data is lost on restart
- Not suitable for persistent messaging
- Memory usage grows with topics and history size

## Limitations & Known Issues

1. **No Persistence**: All data is in-memory and lost on restart
2. **Single Server**: No distributed support or horizontal scaling
3. **Memory Bounded**: Message history is capped at 100 messages per topic
4. **No Authentication**: Open access to all endpoints
5. **No Message TTL**: Messages stay in history until displaced
6. **Global Lock**: Single lock may limit throughput under high concurrency

### WebSocket Disconnects
- Check network stability
- Implement ping/pong keep-alive in client
- Monitor server logs for errors

### High Memory Usage
- Reduce message history size in code
- Delete unused topics
- Limit message payload size


## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **WebSockets**: Real-time bidirectional communication
- **Uvicorn**: Lightning-fast ASGI server
- **Pydantic**: Data validation using Python type annotations
- **asyncio**: Python's asynchronous I/O framework
