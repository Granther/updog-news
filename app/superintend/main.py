# Superintendent, controls the website, can remove posts and change them
# Runs on multiple chat 'threads', combining chat data to a central mind
# Acts using special tokens to, remove, edit stories
# Can judge stories and remove them if it doesnt like them
# A superintendant for the site, complete control and understanding cause why not lol

import os
import threading
import queue

from openai import OpenAI
from groq import Groq

from app.logger import create_logger

# Hoodlem 
# Runs in his own thread, basically uses an API to be interacted with
# How do we start him? Maybe in run.py

# Perm storage
# We need permanent storage to persist through reboots 

# Combining
# Every chat performs an 'integration', where the 

# Need a queue for processing multiple chats with one api key
# Way for the ai to keep close to user context and larger view context (mayber RAG)

users = {
    1: [{"role": "user", "content": "My name is bob1"}],
    2: [{"role": "user", "content": "My name is bob2"}],
}

class SuperIntend:
    """ Groq for fast, feather for slow but custom """
    def __init__(self, groq_key: str, feather_key: str):
        self.logger = create_logger(__name__)
        self.groq, self.feather = self._init_clients(groq_key, feather_key)
        self._init_queue()
        self.logger.debug("Created Superintendent")
    
    """ Start chat queue """
    def _init_queue(self):
        self.logger.debug("Initializing chat queue")
        self.chat_queue = queue.Queue()
        def worker():
            while True:
                messages = self.chat_queue.get()
                resp = self._groq_chat(messages)
                # Send resp back with callback, then send to frontend async
                self.logger.debug(f"Hoodlem resp: {resp}")
                self.chat_queue.task_done()
        # Run in new thread
        threading.Thread(target=worker, daemon=True).start()

    """ Init both Groq and Feather clients """
    def _init_clients(self, groq_key, feather_key):
        self.logger.debug("Creating Groq and Featherless clients")
        return (Groq(api_key=groq_key), 
                OpenAI(
                    base_url="https://api.featherless.ai/v1",
                    api_key=feather_key,
                )
            )

    """ Top level chat func, highest level call """
    def chat(self, msg: str, user_id: int) -> str:
        user_messages = self._get_user_messages(user_id)
        print(user_messages)
        user_messages.append({"role": "user", "content": msg})
        self.chat_queue.put(user_messages)

    """ Given a user's id, return their messages [dict...] AI chat history """
    def _get_user_messages(self, user_id: int) -> list:
        return users[user_id]

    """ Takes list of past messages, sys promt etc and produces a response """
    def _groq_chat(self, messages: list) -> str:
        chat_completion = self.groq.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content


    
        
        

