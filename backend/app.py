import os
from datetime import datetime

import redis
from flask import Flask, jsonify

app = Flask(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None


def get_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


@app.get("/api/ping")
def ping():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] received /api/ping request", flush=True)

    redis_status = "ok"
    ping_count = None

    try:
        client = get_redis_client()
        ping_count = client.incr("ping_count")
    except Exception as exc:
        redis_status = f"error: {exc}"

    return jsonify(
        {
            "status": "ok",
            "service": "flask-backend",
            "redis": redis_status,
            "ping_count": ping_count,
        }
    )


@app.get("/")
def index():
    return jsonify({"message": "Cloud Computing Course Project Backend"})

#1
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
