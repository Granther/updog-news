import threading
import queue

q = queue.Queue()

def worker():
    while True:
        item = q.get()
        print(item)
        q.task_done()

def start_queue():
    threading.Thread(target=worker, daemon=True).start()

def put(item: dict):
    q.put(item)
