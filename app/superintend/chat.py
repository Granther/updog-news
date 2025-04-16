""" Chat class, handling uuids, talking to core, and RAG """

"""
Should we talk to main here? Via some sort of API, like
"Hey, super, I'm talking to so and so and they said that they dont like the most recent thing on the site"
Hoodlem should be able to query the core from here, whats going on, shouldn't WE actually just be the core
Hoodlem is the speaking part of superintend, he know all as well 

We have to have an API of some sort that allows hoodlem to request with context

Hoodlem needs a way to do things, like drop a link, redirect, get info from a story 
"""
import sys
import copy

from app.config import HoodlemConfig
from app.logger import create_logger
from .prompts import ephem_sys_prompt
from .utils import build_client

logger = create_logger(__name__)

class HoodChat:
    def __init__(self, config: HoodlemConfig, core):
        self.config = config
        self.hoodlem = config.HOODLEM_MODEL
        self.sys_prompt = ephem_sys_prompt
        self.core = core
        self.ephem_messages = dict() # uuid: messages        
        try:
            self.hoodlem.set_client(build_client(self.hoodlem, config.KEYS))
        except Exception as e: # Want to exit 'special' when we know we cant continue without this module
            logger.fatal(f"Fatal error while instantiating Hoodlem: {e}")
            sys.exit(1)

    """ Takes UUID and message from user """ 
    def chat(self, uuid: str, message: str) -> str:
        self._append_ephem_messages(uuid, {"role": "user", "content": message})
        messages = self._get_ephem_messages(uuid) # Get copy, things done next dont stick

        #rag_content = self._get_rag(uuid, messages)
        #if rag_content:
        #    self._append_ephem_messages(uuid, {"role": "user", "content": f"{message}\n!### CONTEXT ###!\n{rag_content}"})

        self._append_ephem_messages(uuid, {"role": "system", "content": self.sys_prompt})
        messages = self._get_ephem_messages(uuid)
        return self.core.chat(messages, model=self.hoodlem)

    """ Same as chat but returns generator """
    def chat_stream(self, uuid: str, message: str):
        self._append_ephem_messages(uuid, {"role": "user", "content": message})
        messages = self._get_ephem_messages(uuid) # Get copy, things done next dont stick
        self._append_ephem_messages(uuid, {"role": "system", "content": self.sys_prompt})
        messages = self._get_ephem_messages(uuid)
        return self.core.chat_stream(messages, model=self.hoodlem)

    def _get_rag(self, uuid: str, messages: list) -> str:
        messages.append({"role": "user", "content": "Before you answer the above user's question and given the conversation so far, you you believe past information is needed to properly respond in this conversation? Yes if: The user is asking about past conversations with THIS AI. No if: The user is not referencing anything from the past. Please answer with yes or no. You may only answer with yes OR no, any other response will not be accepted"})
        need_rag_resp = self.core.chat(messages)
        if 'yes' in need_rag_resp.lower():
            messages.append({"role": "user", "content": "Given the conversation so far please create one summarrizing sentence that embodies the sentiment, topic and/or important information that identifies this conversation. Ie, names, recalled events, things said, articles referenced so far. Only use information mentioned in the current conversation"})
            ret_sent = self.core.chat(messages)
            return self.core.query("chats", ret_sent, bad_uuid=uuid)
        return None

    """ Given a unique, one time uuid, return the messages for the ephem chat """
    def _get_ephem_messages(self, uuid: str) -> list:
        if uuid not in self.ephem_messages:
            self.ephem_messages[uuid] = self.core.get_messages()
            return self.ephem_messages[uuid]
        return copy.copy(self.ephem_messages[uuid])

    def _append_ephem_messages(self, uuid: str, chunk: dict):
        messages = self._get_ephem_messages(uuid)
        messages.append(chunk)
        self.ephem_messages[uuid] = messages
