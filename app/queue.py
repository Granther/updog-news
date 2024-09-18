from rq import Queue
from redis import Redis

from app.infer import generate

class QueueManager:
    def __init__(self):
        redis_conn = Redis()
        self.q = Queue(connection=redis_conn)

    def queue_story(self, uuid: str):
        if self.q.enqueue(generate, uuid):
            return True
        return False

_manager = QueueManager()

def queue_story(uuid: str):
    return _manager.queue_story(uuid)