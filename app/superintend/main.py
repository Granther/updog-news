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
#from app.superintend import ephem_sys_prompt

ephem_sys_prompt = "You are a helpful ai"

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
    def __init__(self, groq_key: str, feather_key: str, groq_core_key: str):
        self.logger = create_logger(__name__)
        self.ephem_sys_prompt = ephem_sys_prompt
        self.ephem_messages = dict()
        self.groq, self.feather = self._init_clients(groq_key, feather_key)
        self.core = Core(self._init_groq_client(groq_core_key))
        self.groq_model = "llama-3.3-70b-versatile"
        self._init_queue()
        self.logger.debug("Created Superintendent")
    
    """ Start chat queue """
    def _init_queue(self):
        self.logger.debug("Initializing chat queue")
        self.chat_queue = queue.Queue()
        def worker():
            while True:
                func, args = self.chat_queue.get()
                print("Returns: ", func(*args))
                self.chat_queue.task_done()
        # Run in new thread
        threading.Thread(target=worker, daemon=True).start()

    """ Init both Groq and Feather clients """
    def _init_clients(self, groq_key, feather_key):
        self.logger.debug("Creating Groq and Featherless clients")
        return ((self._init_groq_client(groq_key), self._init_feather_client(feather_key)))

    def _init_groq_client(self, groq_key: str):
        return Groq(api_key=groq_key)

    def _init_feather_client(self, feather_key: str):
        return OpenAI(
                    base_url="https://api.featherless.ai/v1",
                    api_key=feather_key,
                )

    """ Top level chat func, highest level call """
    def chat(self, uuid: str, msg: str) -> str:
        print("HEEERRR")
        self._append_ephem_messages(uuid, {"role": "system", "content": self.ephem_sys_prompt})
        self._append_ephem_messages(uuid, {"role": "user", "content": msg})
        messages = self._get_ephem_messages(uuid)
        self.chat_queue.put((self._groq_chat, (uuid, messages))) # pass callback
        self.chat_queue.join()

    '''
    def chat_with_stream(self, msg: str, user_id: int):
        user_messages = self._get_user_messages(user_id)
        user_messages.append({"role": "user", "content": msg})
        self.chat_queue.put((self._groq_chat_stream, user_messages)) # pass callback
        self.chat_queue.join()
    '''

    """ Given a unique, one time uuid, return the messages for the ephem chat """
    def _get_ephem_messages(self, uuid: str) -> list:
        if uuid not in self.ephem_messages:
            self.ephem_messages[uuid] = []
            return []
        return self.ephem_messages[uuid]

    def _append_ephem_messages(self, uuid: str, chunk: dict):
        messages = self._get_ephem_messages(uuid)
        messages.append(chunk)
        self.ephem_messages[uuid] = messages

    """ Takes list of past messages, sys promt etc and produces a response """
    def _groq_chat(self, uuid: str, messages: list) -> str:
        chat_completion = self.groq.chat.completions.create(
            messages=messages,
            model=self.groq_model,
        )
        resp = chat_completion.choices[0].message.content
        self._append_ephem_messages(uuid, ({"role": "assistant", "content": resp}))
        return resp

    def _groq_chat_stream(self, messages: list):
        response = self.groq.chat.completions.create(
            model=self.groq_model,
            messages=messages,
            stream=True,
        )

        partial_message = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                partial_message = partial_message + chunk.choices[0].delta.content
                # Some kind of encoding error occurs in the SSE, this fixes it
                partial_message = partial_message.replace('\n', '<br>').replace('\r', '<br>')
                yield f"data: {partial_message}\n\n"

        yield "event: end\n"
        yield "data: done\n\n"

""" Main conscience instance, uses api to interact with 
    - Keeps embedding db for RAG
    - No one chats with this, only for core logic and data recall
"""
class Core:
    """ Takes a premade groq client """
    def __init__(self, client):
        self.groq = client

    """ Inform the central AI of changes, important data, etc 
        - We dont expect a response
        - We call this to inform the model often (ie, user visited page)
    """
    def inform(self, data):
        pass
    """ Ask the central AI for some data 
        - We expect a response of some kind
    """
    def query(self, question) -> str:
        pass
    """ Takes list of past messages, sys promt etc and produces a response """
    def _groq_chat(self, messages: list) -> str:
        chat_completion = self.groq.chat.completions.create(
            messages=messages,
            model=self.groq_model,
        )
        return chat_completion.choices[0].message.content

"""
Example:

User visits hoodlem
Logic: Dispatches new instance with clean message history
Not every message should go through the central AI

"""


# What if the main chat process dispatches other threads to complete processes
# So the consiciousness exists as one thread handling high view context and passes RAGed elements to its children
# Can produce a special token to open new line of consiousness
# Main thought happens with a groq, clean, model. Use a featherless model to convert its output to hoodlem
# Adds 'editors notes' while writing the article to use for sources and other things later
# Doesnt use user id to get past data, embed it, can remind the ai. 
    # "Remember me, my names bob, I was the one that said I dont like the most recent Joe Biden article"
    # Embed all chat data
# Use multiple API keys in a rotating setup
# Onion model, central 'pillar' thread runs. Each dispatched instance is doing something and reporting it to the mian thread. I am talking to an instance which can talk to the main pillar 

# Main thread
# - 
        
        

