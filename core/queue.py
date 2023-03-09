from rq import Queue
from redis import Redis


def get_redis_queue(name: str, url: str) -> Queue:
    redis_conn = Redis.from_url(url)
    return Queue(name=name, connection=redis_conn)
