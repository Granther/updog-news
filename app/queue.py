import threading

from rq import Queue
from redis import Redis
from flask import current_app

from app import db
from app.routes import main
from app.infer import generate_news, generate
from app.models import QueuedStory

# app = create_app()

class QueueManager:
    def __init__(self):
        redis_conn = Redis()
        self.q = Queue(connection=redis_conn)

    def queue_story(self, uuid: str):
        """Process a story in a separate thread."""

        # if self.q.enqueue(generate, uuid):
        #     return True
        # return False
    
        app = current_app._get_current_object()  

        def process_in_thread(uuid):
            """Run inside a new thread."""

            with app.app_context(): 
                self.q.enqueue(generate, uuid)

                # story = QueuedStory.query.filter_by(uuid=uuid).first()
                # print(generate_news(title=story.title, guideline=story.guideline, model="meta-llama/Meta-Llama-3.1-8B-Instruct"))

        thread = threading.Thread(target=process_in_thread, args=(uuid,))
        thread.start()

_manager = QueueManager()

def queue_story(uuid: str):
    return _manager.queue_story(uuid)

