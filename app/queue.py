from rq import Queue
from redis import Redis

from app.infer import generate_news, generate
from app.models import QueuedStory

class QueueManager:
    def __init__(self):
        redis_conn = Redis()
        self.q = Queue(connection=redis_conn)

    def queue_story(self, uuid: str):
        # if self.q.enqueue(generate, uuid):
        #     return True
        # return False
    
        story = QueuedStory.query.filter_by(uuid=uuid).first()
        print(generate_news(title=story.title, guideline=story.guideline, model="meta-llama/Meta-Llama-3.1-8B-Instruct"))

_manager = QueueManager()

def queue_story(uuid: str):
    return _manager.queue_story(uuid)