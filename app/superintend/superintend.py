import os
import sys
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
from app.news import get_stories, get_marquee
from app.config import SuperintendConfig, Model
from .prompts import ephem_sys_prompt, superintend_sys_prompt, bool_question_prompt, build_rag, build_need_rag_prompt, build_allow_story, build_doc_ret_prompt, build_interviewy_prompt, build_interviewer_prompt, get_interviewy_person, get_interviewer_person, build_quick_fill, get_iview_title, build_fix_schrod_title, build_periodic_prompt, periodic_sys_prompt
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
    def __init__(self, config):
        self.config = config
        self.dec_toks = 3
        try:
            # Core: Handles internal system management and dishing out jobs. Infer layer
            self.core = Core(config.CORE)
            # Hoodlem: User interaction part of Super. Uses core to perform system tasks during chat
            self.hoodlem = HoodChat(config.HOODLEM, core=self.core)
            # News: News & interview etc generation and infer management
            self.news = News(config.NEWS, core=self.core)
            self._init_queue()
            self.core.set_periodic(self.periodic, event_num=config.EVENT_NUM)
        except Exception as e:
            logger.fatal(f"Fatal error occured while instantiating Superintend: {e}")
            sys.exit(1)
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

    def _bool_question(self, question: str) -> bool:
        messages = [
            {"role": "system", "content": bool_question_prompt},
            {"role": "user", "content": question},
        ]
        resp = self.core.chat(messages)
        if 'no' in resp.lower():
            return False
        elif 'yes' in resp.lower():
            return True
        else:
            logger.fatal(f"Bool question got answer: {resp}")
            return False

    """ Gets called when Superintend needs to be active """
    def periodic(self):
        logger.debug("Periodic callback called for Superintendent")
        # Ask superintend a whole bunch of questions?
        # Change sliding text
        # Change size of some stories
        # Make changes according to what Hoodlem reported
            # Remove story

        def _per():
            stories = get_stories()
            sliding_titles = get_marquee()
            sys = periodic_sys_prompt
            prompt = build_periodic_prompt(dec_toks=self.dec_toks, temp=72, stories=stories, sliding_titles=sliding_titles)
            resp = self.core.request(prompt, sys_prompt=sys, sticky=True, quick=False, dimentia=False)
            if not self._postproc_periodic(resp):
                return False

        max_fails, fails = 5, 0
        dec_toks = self.dec_toks
        for i in range(dec_toks):
            if fails >= max_fails:
                return
            if not _per():
                fails += 1
        
    def _postproc_periodic(self, content: str):
        try:
            tok_field = content.split("Decision Token:")[1]
        except Exception as e:
            logger.fatal(f"Failed to postprocess periodic for decision token: {e}")
            return False

        if "<|DECIDE_CREATE|>" in tok_field:
            print("Got create")
            return self._dec_create()
        elif "<|DECIDE_RM|>" in tok_field:
            print("Got rm")
            return True
        elif "<|DECIDE_SLIDING|>" in tok_field:
            print("Got sliding")
            return True
        elif "<|DECIDE_TMP|>" in tok_field:
            print("Got tmp")
            return True
        elif "<|DECIDE_SIZE|>" in tok_field:
            print("Got size")
            return True
        else:
            return False

    def _dec_create(self) -> bool:
        stories = get_stories()
        sys = build_periodic_sys_prompt(dec_toks=self.dec_toks, temp=72, stories=stories, sliding_titles=sliding_titles)
        resp = self.core.request("", sys_prompt=sys, sticky=True, quick=False, dimentia=False)

_superintend = SuperIntend(SuperintendConfig())
print(_superintend.config)

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

"""
How should superintend periodically become active
- Get status of system after X events
- Schedule
    - Problem is a decay of the site even if no one is there

"""