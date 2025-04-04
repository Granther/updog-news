""" Chat class, handling uuids, talking to core, and RAG """

"""
Should we talk to main here? Via some sort of API, like
"Hey, super, I'm talking to so and so and they said that they dont like the most recent thing on the site"
Hoodlem should be able to query the core from here, whats going on, shouldn't WE actually just be the core
Hoodlem is the speaking part of superintend, he know all as well 

We have to have an API of some sort that allows hoodlem to request with context
"""

class HoodChat:
    def __init__(self, sys_prompt, core):
        self.sys_prompt = sys_prompt
        self.core = core
        self.ephem_messages = dict() # uuid: messages        

    """ Takes UUID and message from user """ 
    def chat(self, message: str):
        self._append_ephem_messages(uuid, {"role": "system", "content": self.sys_prompt})
        self._append_ephem_messages(uuid, {"role": "user", "content": message})
        messages = self._get_ephem_messages(uuid) # Get copy, things done next dont stick
        messages.append({"role": "user", "content": "Before you answer the above user's question and given the conversation so far, you you believe past information is needed to properly respond in this conversation? Yes if: The user is asking about past conversations with THIS AI. No if: The user is not referencing anything from the past. Please answer with yes or no. You may only answer with yes OR no, any other response will not be accepted"})
        need_rag_resp = self.core.request(
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
