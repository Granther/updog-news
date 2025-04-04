""" Handles central AI context, merging, branching, pruning """

from datetime import datetime

# What if we just have a have na incrementing id

""" The messages object, allows for loading and appending """
class Messages:
    def __init__(self, messages):
        self.messages = messages
        self.timed_msgs = dict()

    """ Lets you append messages to the instance messages, these will be added to the main pool later """
    def append(self, message: dict):
        self.timed_msgs[datetime.now()] = message
        self.messages.append(message)

    """ Reads out the list will all appends, this is for chat completion """
    def read(self) -> list:
        return self.messages

    """ Reads out only the appended chat completions, but they contain a timestamp key """
    def read_timestamps(self) -> dict:
        return self.timed_msgs

class CoreMessages:
    def __init__(self):
        # Timestamp and user or assistant chat item, unsorted
        self.messages = dict()

    def __enter__(self):
        return Messages(self._get_messages())

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            print(exc_type, exc_val, exc_tb)
            return True
        return False

    """ Take the new timestamped messages and add them to the main pool """
    def update_timed_msgs(self, new_times: dict):
        for key, val in new_times.items():
            if val['role'] == 'system':
                continue
            self.messages[key] = val 

    """ Retrieves the sorted list of dicts that is the chat history """
    def _get_messages(self) -> list:
        if not self.messages:
            return []
        sorted_dict = sorted(self.messages.items(), key=lambda item: item[0])
        vals = []
        for date, val in sorted_dict:
            vals.append(val)
        return vals

    def _get_timestamped_msgs(self):
        return self.messages


