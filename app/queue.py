import threading

from rq import Queue
from redis import Redis
from flask import current_app

from app import db
from app.routes import main
from app.infer import generate_news, generate
from app.models import QueuedStory

class QueueManager:
    def __init__(self):
        redis_conn = Redis()
        self.q = Queue(connection=redis_conn)

    def queue_story(self, uuid: str):
        """Process a story in a separate thread."""
    
        app = current_app._get_current_object()  

        def process_in_thread(uuid):
            """Run inside a new thread."""

            with app.app_context(): 
                story = QueuedStory.query.filter_by(uuid=uuid).first()
                print("From queue_story", story.title)

                self.q.enqueue(generate, story.title, story.guideline, on_success=self.finish_queue, )
                print("Does this run?")

        thread = threading.Thread(target=process_in_thread, args=(uuid,))
        thread.start()

    def finish_queue(story: str):
        print(story)

_manager = QueueManager()

def queue_story(uuid: str):
    return _manager.queue_story(uuid)

def finish_queue(story: str):
    return _manager.finish_queue(story)

