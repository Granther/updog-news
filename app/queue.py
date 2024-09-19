import threading

from rq import Queue
from redis import Redis
from flask import current_app

from app import db, rq
from app.infer import generate

class QueueManager:
    def __init__(self):
        redis_conn = Redis()
        self.q = Queue(connection=redis_conn)

    def queue_story(self, uuid: str):
        """Process a story in a separate thread."""
    
        app = current_app._get_current_object()  
        with app.app_context():
            generate.queue(uuid)

_manager = QueueManager()

def queue_story(uuid: str):
    return _manager.queue_story(uuid)

# def finish_queue():
#     return _manager.finish_queue()


# def process_in_thread(uuid):
#     """Run inside a new thread."""

#     with app.app_context(): 
#         story = QueuedStory.query.filter_by(uuid=uuid).first()
#         print("From queue_story", story.title)

#         self.q.enqueue(huh, story.title, story.guideline, on_success=finish_queue)

# thread = threading.Thread(target=process_in_thread, args=(uuid,))
# thread.start()

# def queue_story(self, uuid: str):
#     current_app.redis_client.lpush("queue", uuid)

# def finish_queue(job, connection, result, *args, **kwargs):
#     """Callback function to be executed when the job finishes."""

#     print(f"Job {job.id} completed with result: {result}")