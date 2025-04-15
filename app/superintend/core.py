import os
import copy
import datetime
import threading
import queue
import time
import sys
from concurrent.futures import Future

from openai import OpenAI
from groq import Groq
import shortuuid
from dotenv import load_dotenv

from app.logger import create_logger
from app.config import Keys, Model, CoreConfig
from .prompts import ephem_sys_prompt, superintend_sys_prompt, bool_question_prompt, build_rag, build_need_rag_prompt, build_allow_story, build_doc_ret_prompt
from .utils import stringify, postproc_r1, bool_resp, build_client
from .messages import CoreMessages

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
    def __init__(self, config: CoreConfig):
        self.config = config
        self.collections = dict()
        self.max_infer_tries = config.MAX_INFER_TRIES
        self.main = config.CORE_MODEL
        self.quick = config.CORE_QUICK_MODEL
        try:
            # We pair the new client with the model. So now we use main or quick in _infer
            self.main.set_client(build_client(self.main.name, config.KEYS))
            self.quick.set_client(build_client(self.quick.name, config.KEYS))
            self.core_messages = CoreMessages()
            self.chroma = chromadb.PersistentClient(path="./chroma")
            self._init_queue()
            self.collections['main'], self.collections['chats'], self.collections['quotes'], self.collections['titles'] = self._init_collections()
        except Exception as e:
            logger.fatal(f"Fatal error occured while instantiating Core: {e}")
            sys.exit(1)
        self._init_super()

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

    """ Get or create all needed chroma collections """
    def _init_collections(self):
        logger.debug("Creating 'main', 'chats', and 'quotes' vector collections")
        return (self.chroma.get_or_create_collection(name="main"), self.chroma.get_or_create_collection(name="chats"), self.chroma.get_or_create_collection(name="quotes"), self.chroma.get_or_create_collection(name="titles"))

    """ Inform the central AI of changes, important data, etc 
        - We dont expect a response, but we see if it does any API calls
        - We call this to inform the model often (ie, user visited page)
        - Inform does not need a response, we can just add it to the messages, so the next resp will have Informs as context
    """
    def inform(self, data: str):
        with self.core_messages as msgs:
            msgs.append({"role": "user", "content": f"INFORM: {self._add_timestamp(data)}"})
            self.core_messages.update_timed_msgs(msgs.read_timestamps()) # Update central, merge
            logger.debug(f"Made inform of: {data}")

    """ Request an answer, passing quick forks the conscienceness. Sticky meaning wether the request ends up in the core message stream or not
    Basically, is it important or will it clog up superintend?
    """
    def request(self, request: str, sys_prompt: str=None, quick: bool=False, sticky: bool=True) -> str:
        sys = (superintend_sys_prompt if not sys_prompt else sys_prompt)
        with self.core_messages as msgs:
            msgs.append({"role": "system", "content": sys})
            msgs.append({"role": "user", "content": f"REQUEST: {self._add_timestamp(request)}"})
            model = (self.quick if quick else self.main)
            resp = self._submit_task(self._infer, (msgs.read(), model)) # We want to see thinking toks in history
            msgs.append({"role": "assistant", "content": resp})
            if sticky:
                self.core_messages.update_timed_msgs(msgs.read_timestamps()) # Update central, merge
            logger.debug(f"Made request of: {request}, Sticky: {sticky}")
            return resp

    def _infer(self, messages: list, model: Model):
        logger.debug(f"Executing _infer with model: {model}")
        tries = 0
        chat_completion = None
        while tries < self.max_infer_tries:
            try:
                chat_completion = model.client.chat.completions.create(
                    messages=messages,
                    model=model.name
                )
                break
            except Exception as e:
                logger.debug(f"_infer got exception: {e}, Trying {self.max_infer_tries-tries} more times...")
                time.sleep(3) # Give the API a rest :)
                tries += 1

        if tries >= self.max_infer_tries:
            raise Exception(f"Max tries of {self.max_infer_tries} exceeded for _infer")

        resp = chat_completion.choices[0].message.content
        if 'deepseek' in model.name:
            resp = postproc_r1(resp)
        return resp

    """ Hoodlem func, takes chat completions, already RAGed, returns a chat response 
        - Expectation that the caller is handling all chats
        - Simply takes completions and completes them
    """
    def chat(self, messages: list, quick: bool=False) -> str:
        # Uses context of Core, but does not participate, one way so to speak
        model = (self.quick if quick else self.main)
        return self._submit_task(self._infer, (messages, model))

    """ Same as chat but returns a generator for the stream """
    def chat_stream(self, messages: list, quick: bool=False):
        model = (self.quick if quick else self.main)
        return self._submit_task(self._infer_stream, (messages, model))

    """ Ask the central AI for some data 
        - We expect a response of some kind
    """
    def query(self, col_name: str, question: str, n_results: int=3, bad_uuid: str=None, bad_doc: str=None, metadata: dict=None) -> list:
        logger.debug(f"Making query of question: {question} to collection: {col_name}")
        try:
            col = self._get_col(col_name)
            if not col:
                raise Exception(f"VectorDB collection: {col_name} does not exist when trying to query for question: {question}")
            result = col.query(query_texts=[question], where=metadata, n_results=n_results)
            ids = result['ids'][0]
            docs = result['documents'][0]
            if not bad_uuid and not bad_doc:
                return docs
            vals = []
            if bad_uuid:
                for i in range(n_results):
                    if ids[i] != bad_uuid:
                        vals.append(docs[i])
                return vals
            elif bad_doc:
                for i in range(n_results):
                    if docs[i].lower() != bad_doc.lower():
                        vals.append(docs[i])
                return vals
        except Exception as e:
            logger.fatal(e)
            self.inform(e)
        return []

    """ Given a list of QA interviews, embed each quote with the interview uuid metadata """
    def embed_interview(self, content: list, uuid: str):
        logger.debug(f"Embedding interview of uuid: {uuid}")
        def _embed():
            col = self._get_col("quotes")
            for item in content:
                col.add(documents=[item['question']], metadatas=[{"interview_uuid": uuid, "type": "question"}], ids=[shortuuid.uuid()])
                col.add(documents=[item['answer']], metadatas=[{"interview_uuid": uuid, "type": "answer"}], ids=[shortuuid.uuid()])
        threading.Thread(target=_embed, daemon=True).start()

    """ Embed list of contents to collection 'col'. Ids are chosen randomly """
    def embed(self, content: list, col_name: str):
        def _embed():
            try:
                col = self._get_col(col_name)
                if not col:
                    raise Exception(f"Unable to embed len: {len(content)} contents to vectordb collection {col_name}. It does not exist")
                ids = [shortuuid.uuid() for i in range(len(content))]
                col.add(documents=content, ids=ids)
            except Exception as e:
                logger.fatal(e)
                self.inform(e)
        threading.Thread(target=_embed, daemon=True).start()

    """ Gets the core context for superintendent """
    def get_messages(self) -> list:
        return self.core_messages._get_messages()

    """ See if API tokens exist in reponse and call things accordingly """
    def _postproc_chat(self, response: str):
        pass

    def _add_timestamp(self, data: str) -> str:
        return f"{datetime.datetime.now()}: {data}"

    def replace_doc(self, col_name: str, uuid: str, doc):
        col = self._get_col(col_name)
        try:
            col.delete(ids=[uuid])
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
    # def _groq_chat(self, messages: list, model: str) -> str:
    #         logger.debug(f"Executing groq_chat with model: {model}")
    #         tries = 0
    #         max_tries = 3
    #         chat_completion = None
    #         while tries < max_tries:
    #             try:
    #                 chat_completion = self.groq.chat.completions.create(
    #                     messages=messages,
    #                     model=(self.groq_model if not model else model)
    #                 )
    #                 break
    #             except Exception as e:
    #                 logger.debug(f"Groq chat got exception: {e}, Trying {max_tries-tries} more times...")
    #                 time.sleep(3) # Give the API a rest :)
    #                 tries += 1

    #         if tries >= max_tries:
    #             raise Exception(f"Max tries of {max_tries} exceeded for groq_chat")

    #         resp = chat_completion.choices[0].message.content
    #         if 'deepseek' in self.groq_model:
    #             resp = postproc_r1(resp)
    #         return resp

    def _infer_stream(self, messages: str, model: str): 
        stream = model.client.chat.completions.create(
            messages=messages,
            model=model.name,
            stop=None,
            stream=True,
        )
        return stream

    def _fill_chats(self):
        col = self._get_col("chats")
        col.add(documents=["test1", "test2", "test3"], ids=["1", "2", "3"])

