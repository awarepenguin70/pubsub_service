# In-Memory Pub/Sub System

This project is a simplified, in-memory Publish/Subscribe system implemented in Python using the FastAPI framework. It provides real-time messaging over a WebSocket endpoint and management capabilities via a REST API, all within a 2-hour time constraint.

## Features

- **Real-Time Messaging**: Publish messages to topics and receive them in real-time.
- **Topic Management**: Create, delete, and list topics via a REST API.
- **System Observability**: `/health` and `/stats` endpoints for monitoring.
- **Concurrency Safe**: Designed to handle multiple publishers and subscribers safely.
- **Message Replay**: Supports replaying the last N messages to new subscribers.
- **In-Memory**: No external databases or message brokers are required. State is not persisted across restarts.

## API Reference

### REST Endpoints

- `POST /topics`: Creates a new topic.
- `DELETE /topics/{name}`: Deletes a topic and disconnects its subscribers.
- `GET /topics`: Lists all topics and their subscriber counts.
- `GET /health`: Provides system health and uptime.
- `GET /stats`: Provides detailed message and subscriber counts per topic.

### WebSocket (`/ws`) Protocol

The WebSocket endpoint supports `subscribe`, `unsubscribe`, `publish`, and `ping` actions. Please refer to the assignment specification for detailed JSON message formats.

## Getting Started (Local Development)

### Prerequisites

- Python 3.9+
- `pip` and `venv`

### Design Decisions & Assumptions

Concurrency Model
The system uses a single, global asyncio.Lock to serialize access to all shared in-memory state (topics, subscribers, etc.).

Reasons:

Correctness: Prevents race conditions, ensuring data consistency under concurrent load.

Implementation Speed: Simple to implement correctly, which is important given the time constraint.

This approach prioritizes correctness and development speed over raw performance.

Backpressure Policy
The system implements an implicit backpressure mechanism:

When a message is published, the server iterates through all subscribers and awaits websocket.send_json() for each.

Fast subscribers complete quickly.

Slow subscribers naturally throttle the publisher due to awaiting on full network buffers.

The policy slows down the publisher instead of disconnecting clients or dropping messages. No per-subscriber message queue is implemented.

Message History & Replay
Each topic maintains a collections.deque with a fixed size (maxlen=100) to store the most recent messages, providing an efficient ring buffer for the last N replay feature. The size is hardcoded and not configurable.

### Installation & Running

1. Clone the repository:

```bash
git clone <repository_url>
cd <repository_folder>
Create and activate a virtual environment:

bash
Copy code
python -m venv venv
source venv/bin/activate
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Run the application:

bash
Copy code
uvicorn main:app --reload
The service will be available at http://127.0.0.1:8000.

Running with Docker
Build the Docker image:

bash
Copy code
docker build -t pubsub-service .
Run the Docker container:

bash
Copy code
docker run -d -p 8000:8000 --name pubsub-container pubsub-service
