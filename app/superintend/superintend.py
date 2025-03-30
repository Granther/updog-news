import os
import copy
from time import sleep
import datetime
import threading
import queue
from concurrent.futures import Future

from openai import OpenAI
from groq import Groq
import shortuuid
from dotenv import load_dotenv

from app.logger import create_logger
from .prompts import ephem_sys_prompt, superintend_sys_prompt, bool_question_prompt, build_rag, build_need_rag_prompt, build_allow_story, build_doc_ret_prompt, build_interviewy_prompt, build_interviewer_prompt, get_interviewy_person, get_interviewer_person, build_quick_fill
from .utils import stringify, postproc_r1, bool_resp
from app.models import Interview
from app import db
from .core import Core

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb

load_dotenv()
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
        self.ephem_sys_prompt = ephem_sys_prompt
        self.ephem_messages = dict()
        self.max_interview_q = 2
        self.groq, self.feather = self._init_clients(groq_key, feather_key)
        self.core = Core(self._init_groq_client(groq_core_key))
        self.groq_model = "deepseek-r1-distill-qwen-32b"
        self._init_queue()
        logger.debug("Created Superintendent")
    
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
        need_rag_resp = self._submit_task(self._groq_chat, messages, None)
        if 'yes' in need_rag_resp.lower():
            messages.append({"role": "user", "content": "Given the conversation so far please create one summarrizing sentence that embodies the sentiment, topic and/or important information that identifies this conversation. Ie, names, recalled events, things said, articles referenced so far. Only use information mentioned in the current conversation"})
            ret_sent = self._submit_task(self._groq_chat, messages, None)
            rag_content = self.core.query("chats", ret_sent, bad_uuid=uuid)
            print("Ret sent: ", ret_sent)

        print("Need rag resp: ", need_rag_resp)

        if rag_content:
            #msg = build_rag(msg, rag_content)
            self._append_ephem_messages(uuid, {"role": "user", "content": f"{msg}\n!### CONTEXT ###!\n{rag_content}"})
        messages = self._get_ephem_messages(uuid)
        resp = self._submit_task(self._groq_chat, messages, None) # pass callback
        self._process_chat(resp, uuid)
        return resp

    def raw_chat(self, messages: list) -> str:
        return self._submit_task(self._groq_chat, messages) # pass callback

    """ Takes title, returns (reporter, personality, category """
    def quick_fill(self, title: str):
        logger.debug("Starting Quick fill to core")
        # Use quick model 
        print(self.core.request(build_quick_fill(title), quick=True))
        
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

    def _process_chat(self, response: str, uuid: str):
        self._append_ephem_messages(uuid, ({"role": "assistant", "content": response}))
        self.core.replace_doc("chats", uuid, self.ephem_messages[uuid])

    def _process_actions(self, response: str, uuid: str):
        pass

    """ Generate the 2 personalities for the interview. Interviewer and Interviewy """
    def _gen_interv_persons(self, content: str):
        interviewer = self.core.request(get_interviewer_person(content))
        interviewy = self.core.request(get_interviewy_person(content))
        return (interviewer, interviewy)

    """ Given the story, and interview (name, personality) generate a interview """
    def gen_interview(self, app, content: str) -> str:
        with app.app_context():
            logger.debug("Generating interview")
            n_interview_q = 0
            model = "gemma2-9b-it"
            interviewer = postproc_r1(self.core.request(get_interviewer_person(content)))
            interviewy = postproc_r1(self.core.request(get_interviewy_person(content)))
            viewer_prompt = build_interviewer_prompt(content, interviewer) # The interviewer knows about the story
            viewy_prompt = build_interviewy_prompt(interviewy)
            viewer_messages, viewy_messages = [{"role": "system", "content": viewer_prompt}, {"role": "user", "content": "BEGINNING OF INTERVIEW"}], [{"role": "system", "content": viewy_prompt}]

            logger.debug(f"Interviewer personality: {interviewer}")
            logger.debug(f"Interviewy personality: {interviewy}")

            interview_content = ""
            while n_interview_q < self.max_interview_q:
                # Gen question
                question = postproc_r1(self._submit_task(self._groq_chat, viewer_messages, model)).replace('\n', '')
                sleep(1.5) # Give the API a break so we dont over use

                # Make sure interviewer knows what he asked
                viewer_messages.append({"role": "assistant", "content": question})
                viewer_messages.append({"role": "system", "content": viewer_prompt})

                # Add to interviewy context
                viewy_messages.append({"role": "user", "content": question})
                # Ask them to answer
                answer = postproc_r1(self._submit_task(self._groq_chat, viewy_messages, model)).replace('\n', '')
                sleep(1.5)

                # Make sure personas know what they produces
                viewy_messages.append({"role": "assistant", "content": answer})
                viewy_messages.append({"role": "system", "content": viewy_prompt})
                # Add answer to interviewer context
                viewer_messages.append({"role": "user", "content": answer})
                
                interview_content += f"Q: {question}\nA: {answer}\n\n"
                n_interview_q += 1
            uuid = shortuuid.uuid()
            logger.debug(f"Finished interview with uuid: {uuid}")
            interview = Interview(uuid=uuid, title="Test title", content=interview_content, interviewer="Interviewer", interviewy="Interviewy")
            db.session.add(interview)
            db.session.commit()

    """ Pass in entire story and return wether Super allows it or not """
    def allow_story(self, story) -> bool:
        resp = self.core.request(build_allow_story(story))
        return bool_resp(postproc_r1(resp))

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
            logger.fatal(f"Bool question got answer: {resp}")

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

_superintend = SuperIntend(os.environ.get("GROQ_API_KEY"), os.environ.get("FEATHERLESS_API_KEY"), os.environ.get("GROQ_API_KEY"))

""" Makes Superintend singleton, which makes sense """
def get_superintend():
    return _superintend

""" Takes app for context and entire story to generate interviews """
def gen_sources(app, content: str):
    pass

def gen_interviews(app, story):
    threading.Thread(target=_superintend.gen_interview, args=(app, story.content), daemon=True).start()
"""
Example:

User visits hoodlem
Logic: Dispatches new instance with clean message history
Not every message should go through the central AI

"""

if __name__ == "__main__":
    content = """
    The White House announced today that First Lady Jill Biden is expecting another grandchild. This news comes as a surprise to many, considering the First Lady is already a grandmother to several grandchildren. Some might even say it's a bit, shall we say, "ripe" for a woman her age.

    The announcement was met with predictable fanfare from the usual suspects. The President, naturally, was ecstatic, gushing about how "thrilled" he was. One can only imagine the political machinations behind this announcement, timed perfectly to distract from, well, let's just say the President's recent... "mishaps."

    The White House, predictably, offered no details about the pregnancy, including the due date or the identity of the expecting parents. They did, however, release a photo of the First Lady beaming, clutching a sonogram picture. Let's be honest, the woman's been through enough with her husband's antics. Maybe she's just trying to find something to smile about.

    Naturally, the media is having a field day with this news. Every outlet is running the same tired stories about "family joy" and "expanding the Biden clan." It's enough to make you wonder if they've ever heard of a story that doesn't involve the Bidens.

    We reached out to a few political analysts for their take on the news. "This is classic Biden," one unnamed source told us, "always looking for a way to control the narrative."

    Another analyst, who wished to remain anonymous, offered a more cynical perspective. "Let's be real," he said, "this is just another way for the White House to distract from the real issues facing the country."

    Whether this is a genuine moment of joy or a carefully orchestrated PR stunt, one thing is certain: the news cycle will be dominated by the impending arrival of another Biden grandchild for the foreseeable future.
    """
    _superintend.gen_interview(content)
