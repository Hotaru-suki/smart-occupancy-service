import json
import redis


class RedisHelper:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6379,
        db: int = 1,
        password: str = "",
    ):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password if password else None,
            decode_responses=True,
        )

    def get_json(self, key: str):
        raw = self.client.get(key)
        if not raw:
            return None
        return json.loads(raw)

    def set_json(self, key: str, value: dict):
        self.client.set(key, json.dumps(value, ensure_ascii=False))

    def lrange_json(self, key: str, start: int = 0, end: int = -1):
        items = self.client.lrange(key, start, end)
        return [json.loads(item) for item in items]

    def lpush_json(self, key: str, value: dict):
        self.client.lpush(key, json.dumps(value, ensure_ascii=False))

    def delete_key(self, key: str):
        self.client.delete(key)

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))