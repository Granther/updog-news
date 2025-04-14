import os
import copy
import time
from time import sleep
import datetime
import threading
import queue
from concurrent.futures import Future

from openai import OpenAI
from groq import Groq
import shortuuid

from app.logger import create_logger
from .prompts import ephem_sys_prompt, superintend_sys_prompt, bool_question_prompt, build_rag, build_need_rag_prompt, build_allow_story, build_doc_ret_prompt, build_interviewy_prompt, build_interviewer_prompt, get_interviewy_person, get_interviewer_person, build_quick_fill, get_iview_title, build_fix_schrod_title
from .utils import stringify, postproc_r1, bool_resp, extract_tok_val, pretty_interview
from app.models import Interview
from app import db
from .core import Core
from .chat import HoodChat
from .news import News

logger = create_logger(__name__)

class SuperIntend:
    _instance = None
    _lock = threading.Lock()

    """ For actually creating the instance, not init """
    def __new__(self, *args, **kwargs):
        if self._instance is None:
            with self._lock:  
                if self._instance is None:  
                    self._instance = super(SuperIntend, self).__new__(self)
        return self._instance

    """ Groq for fast, feather for slow but custom """
    def __init__(self, groq_key: str, feather_key: str, groq_core_key: str):
        #self.ephem_sys_prompt = ephem_sys_prompt
        #self.ephem_messages = dict()
        self.groq, self.feather = self._init_clients(groq_key, feather_key)
        self.core = Core(self._init_groq_client(groq_core_key))
        self.hoodlem = HoodChat(ephem_sys_prompt, self.core)
        self.news = News(self.core)
        self.groq_model = "deepseek-r1-distill-qwen-32b"
        self.quick_model = "gemma2-9b-it"
        self._init_queue()
        logger.debug("Created Superintendent")
    
    """ Submit task to be completed on superintend queue """
    def _submit_task(self, func, *args):
        future = Future()
        self.chat_queue.put((func, args, future))
        return future.result() # Blocks until returns

    """ Start chat queue """
    def _init_queue(self):
        logger.debug("Initializing chat queue")
        self.chat_queue = queue.Queue()
        def worker():
            while True:
                func, args, future = self.chat_queue.get()
                try:
                    result = func(*args)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                finally:
                    self.chat_queue.task_done()
        # Run in new thread
        threading.Thread(target=worker, daemon=True).start()

    """ Init both Groq and Feather clients """
    def _init_clients(self, groq_key, feather_key):
        logger.debug("Creating Groq and Featherless clients")
        return ((self._init_groq_client(groq_key), self._init_feather_client(feather_key)))

    def _init_groq_client(self, groq_key: str):
        return Groq(api_key=groq_key)

    def _init_feather_client(self, feather_key: str):
        return OpenAI(
                    base_url="https://api.featherless.ai/v1",
                    api_key=feather_key,
                )

    def _bool_question(self, question: str) -> bool:
        messages = [
            {"role": "system", "content": bool_question_prompt},
            {"role": "user", "content": question},
        ]
        resp = self.core.chat(messages)
        #print(resp)
        if 'no' in resp.lower():
            return False
        elif 'yes' in resp.lower():
            return True
        else:
            return False
            logger.fatal(f"Bool question got answer: {resp}")

_superintend = SuperIntend(os.environ.get("GROQ_API_KEY"), os.environ.get("FEATHERLESS_API_KEY"), os.environ.get("GROQ_API_KEY"))

""" Makes Superintend singleton, which makes sense """
def get_superintend():
    return _superintend

""" Takes app for context and entire story to generate interviews """
def gen_sources(app, content: str):
    pass

# def gen_interviews(app, story):
#     threading.Thread(target=_superintend.gen_interview, args=(app, story), daemon=True).start()
"""
Example:

User visits hoodlem
Logic: Dispatches new instance with clean message history
Not every message should go through the central AI

"""

"""

Ok, so superintend, the high level API is taking care of Chat right now which is wrong.
Should core do it? Hmmm, no, too low level. Separate class? Yes

"""

if __name__ == "__main__":
    pass

#""" Takes list of past messages, sys promt etc and produces a response """
# def _groq_chat(self, messages: list, model: str) -> str:
#     logger.debug(f"Executing groq_chat with model: {model}")
#     tries = 0
#     max_tries = 3
#     chat_completion = None
#     while tries < max_tries:
#         try:
#             chat_completion = self.groq.chat.completions.create(
#                 messages=messages,
#                 model=(self.groq_model if not model else model)
#             )
#             break
#         except Exception as e:
#             logger.debug(f"Groq chat got exception: {e}, Trying {max_tries-tries} more times...")
#             time.sleep(3) # Give the API a rest :)
#             tries += 1

#     if tries >= max_tries:
#         raise Exception(f"Max tries of {max_tries} exceeded for groq_chat")

#     resp = chat_completion.choices[0].message.content
#     if 'deepseek' in self.groq_model:
#         resp = postproc_r1(resp)
#     return resp

# def _groq_chat_stream(self, messages: list):
#     response = self.groq.chat.completions.create(
#         model=self.quick_model,
#         messages=messages,
#         stream=True,
#     )
#     return response
# """
# partial_message = ""
# for chunk in response:
#     if chunk.choices[0].delta.content is not None:
#         partial_message = partial_message + chunk.choices[0].delta.content
#         # Some kind of encoding error occurs in the SSE, this fixes it
#         partial_message = partial_message.replace('\n', '<br>').replace('\r', '<br>')
#         yield f"data: {partial_message}\n\n"

# yield "event: end\n"
# yield "data: done\n\n"
# """