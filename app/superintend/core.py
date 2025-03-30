import os
import copy
import datetime
import threading
import queue
from concurrent.futures import Future

from openai import OpenAI
from groq import Groq
import shortuuid
from dotenv import load_dotenv

from app.logger import create_logger
from .prompts import ephem_sys_prompt, superintend_sys_prompt, bool_question_prompt, build_rag, build_need_rag_prompt, build_allow_story, build_doc_ret_prompt
from .utils import stringify, postproc_r1, bool_resp

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb

load_dotenv()
logger = create_logger(__name__)

""" Main conscience instance, uses api to interact with 
    - Keeps embedding db for RAG
    - No one chats with this, only for core logic and data recall
"""
class Core:
    """ Takes a premade groq client """
    def __init__(self, client):
        self.messages = list()
        self.collections = dict()
        self.groq = client
        self.groq_model = "deepseek-r1-distill-qwen-32b"
        self.quick_model = "gemma2-9b-it"
        self.chroma = chromadb.PersistentClient(path="./chroma")
        self._init_queue()
        self.chats, self.main = self._init_chat_col(), self._init_main_col()
        self.collections['chats'], self.collections['main'] = self.chats, self.main
        self._init_super()
        #self._fill_chats()

    """ First message sent to superintend """
    def _init_super(self):
        self.inform("Updog.news Core booting up... Hello Superintendent from init systems :)")

    """ Start thought queue """
    def _init_queue(self):
        logger.debug("Initializing Superintendent thought queue")
        self.thought_queue = queue.Queue()
        def worker():
            while True:
                func, args, future = self.thought_queue.get()
                try:
                    result = func(*args)
                    future.set_result(result)
                except Exception as e:
                    future.set_exception(e)
                finally:
                    self.thought_queue.task_done()
        # Run in new thread
        threading.Thread(target=worker, daemon=True).start()

    """ Submit task to thought queue, block until return """
    def _submit_task(self, func, *args):
        future = Future()
        self.thought_queue.put((func, *args, future))
        return future.result() # Blocks until returns

    """ Get or create 'chats' chroma collection """
    def _init_chat_col(self):
        return self.chroma.get_or_create_collection(name="chats")

    """ Get or create 'main' chroma collection """
    def _init_main_col(self):
        return self.chroma.get_or_create_collection(name="main")

    """ Inform the central AI of changes, important data, etc 
        - We dont expect a response, but we see if it does any API calls
        - We call this to inform the model often (ie, user visited page)
    """
    def inform(self, data: str):
        self.messages.append({"role": "system", "content": superintend_sys_prompt})
        self.messages.append({"role": "user", "content": f"INFORM: {self._add_timestamp(data)}"})
        resp = self._submit_task(self._groq_chat, (self.messages, self.groq_model)) # Get all toks from R1
        logger.debug(f"INFORM: {data}\nResponse: {resp}")
        self.messages.append({"role": "assistant", "content": resp})

    """ Request an answer, passing quick forks the conscienceness """
    def request(self, request: str, quick: bool=True):
        self.messages.append({"role": "system", "content": superintend_sys_prompt})
        self.messages.append({"role": "user", "content": f"REQUEST: {self._add_timestamp(request)}"})
        model = (self.quick_model if quick else self.groq_model)
        print(model)
        resp = self._submit_task(self._groq_chat, (self.messages, model)) # We want to see thinking toks in history
        self.messages.append({"role": "user", "content": resp}) 
        return resp

    """ Ask the central AI for some data 
        - We expect a response of some kind
    """
    def query(self, col_name: str, question: str, bad_uuid: str=None) -> str:
        col = self._get_col(col_name)
        if not col: 
            return None
        try:
            n_results = 3
            result = col.query(query_texts=[question], n_results=n_results)
            ids = result['ids'][0]
            docs = result['documents'][0]
            if not bad_uuid:
                return docs[0]
            print("bad_uuid: ", bad_uuid)
            for i in range(n_results):
                print(ids[i])
                if ids[i] != bad_uuid:
                    print(docs[i])
                    return docs[i]
        except:
            return None

    """ See if API tokens exist in reponse and call things accordingly """
    def _postproc_chat(self, response: str):
        print(response)

    def _add_timestamp(self, data: str) -> str:
        return f"{datetime.datetime.now()}: {data}"

    def replace_doc(self, col_name: str, uuid: str, doc):
        col = self._get_col(col_name)
        try:
            col.delete(ids=[uuid])
            #if type(doc) is list:
            doc = stringify(doc)
            col.add(documents=[doc], ids=[uuid])
        except Exception as e:
            logger.fatal(f"Unable to replace uuid: {uuid} document: {e}")
     
    def _get_col(self, col_name: str):
        if col_name not in self.collections:
            logger.fatal(f"Passed collection: {col_name}, but it does not exist in Core")
            return False
        return self.collections[col_name]

    """ Takes list of past messages, sys promt etc and produces a response """
    def _groq_chat(self, messages: list, model: str) -> str:
            logger.debug(f"Executing groq_chat with model: {model}")
            tries = 0
            max_tries = 3
            chat_completion = None
            while tries < max_tries:
                try:
                    chat_completion = self.groq.chat.completions.create(
                        messages=messages,
                        model=(self.groq_model if not model else model)
                    )
                    break
                except Exception as e:
                    logger.debug(f"Groq chat got exception: {e}, Trying {max_tries-tries} more times...")
                    time.sleep(3) # Give the API a rest :)
                    tries += 1

            if tries >= max_tries:
                raise Exception(f"Max tries of {max_tries} exceeded for groq_chat")

            resp = chat_completion.choices[0].message.content
            if 'deepseek' in self.groq_model:
                resp = postproc_r1(resp)
            return resp

    def _fill_chats(self):
        col = self._get_col("chats")
        col.add(documents=["test1", "test2", "test3"], ids=["1", "2", "3"])

