import threading
import queue

from app import get_app

from app.news import write_new_story

q = queue.Queue()

def worker():
    while True:
        item = q.get()
        print(item)
        write_new_story(item)
        q.task_done()

def start_queue():
    threading.Thread(target=worker, daemon=True).start()

def put_story(item: dict):
    q.put(item)
