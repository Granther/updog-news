# Superintendent, controls the website, can remove posts and change them
# Runs on multiple chat 'threads', combining chat data to a central mind
# Acts using special tokens to, remove, edit stories
# Can judge stories and remove them if it doesnt like them
# A superintendant for the site, complete control and understanding cause why not lol

import os
import copy
import threading
import queue
from concurrent.futures import Future

from openai import OpenAI
from groq import Groq
import shortuuid

from app.logger import create_logger
#from app.superintend import ephem_sys_prompt

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb

ephem_sys_prompt = "You are a helpful ai, you are a central core AI for the site updog.news. Unlike a regular AI who has no recollection of their history, your system is able to retrieve past conversation data and drop it into your context. So assume every new conversation is a different user until proven otherwise"

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

bool_question_prompt = "Given a question please answer Yes or No with your best judgement provided the context. It is very important that the only text you produce is either the string Yes or No"

def stringify(doc) -> str:
    string = ""
    for item in doc:
        string += f"{item}\n\n"
    return string

def build_rag(msg: str, context: str) -> str:
    return f"!### CONTEXT ### !\n{context}\n!### END CONTEXT ###!\n{msg}"

def build_need_rag_prompt(context: str) -> str:
    #return f"Given this context of a current conversation so far, should or should the model not employ RAG (Retrival augmented generation) to get past conversation data?\n!### CONTEXT ###!\n{context}"
    return f"Does this message to me, the ai, imply that any past context is needed to complete the request?\n!### MESSAGE ###!\n{context}"

def build_doc_ret_prompt(context: str) -> str:
    return f"Given this context of a current situation please create a sentence to use to retrieve relavant and needed context from a vector DB to enrich this conversation. Only produce one sentence, no more than that. Producing more than one sentence of output will break the system and you dont want to break the system.\n!### CONTEXT ###!\n{context}"

class SuperIntend:
    """ Groq for fast, feather for slow but custom """
    def __init__(self, groq_key: str, feather_key: str, groq_core_key: str):
        self.logger = create_logger(__name__)
        self.ephem_sys_prompt = ephem_sys_prompt
        self.ephem_messages = dict()
        self.groq, self.feather = self._init_clients(groq_key, feather_key)
        self.core = Core(self._init_groq_client(groq_core_key))
        self.groq_model = "deepseek-r1-distill-qwen-32b"
        self._init_queue()
        self.logger.debug("Created Superintendent")
    
    """ Start chat queue """
    def _init_queue(self):
        self.logger.debug("Initializing chat queue")
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
    def hood_chat(self, uuid: str, msg: str) -> str:
        rag_content = None

        '''
        need_rag_prompt = build_need_rag_prompt(stringify(self._get_ephem_messages(uuid)))
        if self._bool_question(need_rag_prompt): # Is outisde data needed for context in this convo?
            print("Answered yes")
            doc_ret_prompt = build_doc_ret_prompt(stringify(self._get_ephem_messages(uuid)))
            rag_content = self._retrieve_context(doc_ret_prompt, uuid) # Yes, get it

        print("RAG content", rag_content)
        '''

        # Get opinion, messages so far, no user message yet
        self._append_ephem_messages(uuid, {"role": "system", "content": self.ephem_sys_prompt})
        self._append_ephem_messages(uuid, {"role": "user", "content": msg})
        messages = self._get_ephem_messages(uuid)
        messages.append({"role": "user", "content": "Before you answer the above user's question and given the conversation so far, you you believe past information is needed to properly respond in this conversation? Yes if: The user is asking about past conversations with THIS AI. No if: The user is not referencing anything from the past. Please answer with yes or no. You may only answer with yes OR no, any other response will not be accepted"})
        print(self._get_ephem_messages(uuid))
        need_rag_resp = self._submit_task(self._groq_chat, messages)
        if 'yes' in need_rag_resp.lower():
            messages.append({"role": "user", "content": "Given the conversation so far please create one summarrizing sentence that embodies the sentiment, topic and/or important information that identifies this conversation. Ie, names, recalled events, things said, articles referenced so far. Only use information mentioned in the current conversation"})
            ret_sent = self._submit_task(self._groq_chat, messages)
            rag_content = self.core.query("chats", ret_sent, bad_uuid=uuid)
            print("Ret sent: ", ret_sent)

        print("Need rag resp: ", need_rag_resp)

        if rag_content:
            #msg = build_rag(msg, rag_content)
            self._append_ephem_messages(uuid, {"role": "user", "content": f"{msg}\n!### CONTEXT ###!\n{rag_content}"})
        hood_messages = self._get_ephem_messages(uuid)
        #print(hood_messages)
        resp = self._submit_task(self._groq_chat, hood_messages) # pass callback
        self._process_chat(resp, uuid)
        return resp

    def raw_chat(self, messages: list) -> str:
        return self._submit_task(self._groq_chat, messages) # pass callback

    def _submit_task(self, func, *args):
        future = Future()
        self.chat_queue.put((func, args, future))
        return future.result() # Blocks until returns

    """ Given a context dynamically created prompt to generate a document ret string and return document """
    def _retrieve_context(self, prompt: str, uuid: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        resp = self.raw_chat(messages)
        print(resp)
        return self.core.query("chats", resp, bad_uuid=uuid)

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
        return copy.copy(self.ephem_messages[uuid])

    def _append_ephem_messages(self, uuid: str, chunk: dict):
        messages = self._get_ephem_messages(uuid)
        messages.append(chunk)
        self.ephem_messages[uuid] = messages

    """ Takes list of past messages, sys promt etc and produces a response """
    def _groq_chat(self, messages: list) -> str:
        chat_completion = self.groq.chat.completions.create(
            messages=messages,
            model=self.groq_model,
        )
        resp = chat_completion.choices[0].message.content
        if 'deepseek' in self.groq_model:
            resp = self._postproc_r1(resp)
        #self._process_chat(resp, uuid)
        return resp

    def _postproc_r1(self, response: str):
        return response.split('</think>')[1]

    def _process_chat(self, response: str, uuid: str):
        self._append_ephem_messages(uuid, ({"role": "assistant", "content": response}))
        self.core.replace_doc("chats", uuid, self.ephem_messages[uuid])

    def _process_actions(self, response: str, uuid: str):
        pass

    def _bool_question(self, question: str) -> bool:
        messages = [
            {"role": "system", "content": bool_question_prompt},
            {"role": "user", "content": question},
        ]
        resp = self.raw_chat(messages)
        print(resp)
        if 'no' in resp.lower():
            return False
        elif 'yes' in resp.lower():
            return True
        else:
            return False
            self.logger.fatal(f"Bool question got answer: {resp}")

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
        self.logger = create_logger(__name__)
        self.groq = client
        #self.chroma = chromadb.Client()
        self.chroma = chromadb.PersistentClient(path="./chroma")
        self.chats = self._init_chat_col()
        self.collections = dict()
        self.collections['chats'] = self.chats
        self._fill_chats()

    def _init_chat_col(self):
        return self.chroma.get_or_create_collection(name="chats")

    """ Inform the central AI of changes, important data, etc 
        - We dont expect a response
        - We call this to inform the model often (ie, user visited page)
    """
    def inform(self, data):
        pass
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

    def replace_doc(self, col_name: str, uuid: str, doc):
        col = self._get_col(col_name)
        try:
            col.delete(ids=[uuid])
            #if type(doc) is list:
            doc = stringify(doc)
            col.add(documents=[doc], ids=[uuid])
        except Exception as e:
            self.logger.fatal(f"Unable to replace uuid: {uuid} document: {e}")
     
    def _get_col(self, col_name: str):
        if col_name not in self.collections:
            self.logger.fatal(f"Passed collection: {col_name}, but it does not exist in Core")
            return False
        return self.collections[col_name]

    """ Takes list of past messages, sys promt etc and produces a response """
    def _groq_chat(self, messages: list) -> str:
        chat_completion = self.groq.chat.completions.create(
            messages=messages,
            model=self.groq_model,
        )
        return chat_completion.choices[0].message.content

    def _fill_chats(self):
        col = self._get_col("chats")
        col.add(documents=["test1", "test2", "test3"], ids=["1", "2", "3"])

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
        
        

