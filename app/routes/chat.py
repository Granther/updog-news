import os
from collections import defaultdict
import shortuuid
from queue import Queue

from flask import Blueprint, abort, render_template, session, jsonify, redirect, url_for, current_app, flash, request, stream_with_context, Response
from flask_login import login_required, logout_user, login_user, current_user
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Queue
from uuid import uuid4   
from dotenv import load_dotenv

from app import db, login_manager
from app.models import Story, User
from app.forms import GenerateStoryForm, LoginForm, RegistrationForm, NewReporterForm, CommentForm
from app.utils import preserve_markdown, display_catagory
from app.news import get_marquee, get_stories, write_new_story
from app.queue import put_story, start_queue
from app.superintend import SuperIntend, get_superintend

load_dotenv()
superintend = get_superintend()
chat = Blueprint('chat', __name__,
                        template_folder='templates')

"""
When a user is chatting in the browser, get button press 'send' with msg
chat_with_stream(msg), gets added to superintend queue
When its ready 
"""

two_piece_toks = ["GEN_STORY"]
one_piece_toks = ["KICK"] 

def clean_tok(tok: str) -> str:
    return tok.replace('\n', '').replace(' ', '').replace('\t', '')

""" Takes a special token, QUOTE, and its val, the value between 2 tokens if another token exists, it returns a string to be appended to buffer in its place """
def proc_special(special: str, val: str=None) -> str:
    match special:
        case "KICK":
            print("Going to kick user")
            return "Gonna kick this asshole"

    if val is None:
        raise Exception(f"Token: {special} may expect value, none was passed")

    # 2 Piece token sets
    match special:
        case "GEN_STORY":
            print("Going to generate story: ", val)
            huh = f"<a href=http://localhost:5000/story/{val.replace(' ', '')}>{val}</a>"
            print(huh)
            return huh
    
def next_tok(gen):
    return next(gen).choices[0].delta.content

def chat_tok_generator(message: str):
    max_tok_len = 10
    buffer = ""
    gan = superintend.chat_stream()
    gen = superintend._groq_chat_stream([{"role": "user", "content": message}])
    cur_special = ""
    special_val = ""
    in_special = False
    special_return = ""
    """
    While the generator is still producing words or an exception is not occuring continue 
    If we see the start of a token, <|, we enter it and read its contents until we see it close
    or we reach the max tok len. If the token is a single, we proc it without a val
    If its a double we set in_special=True and read everything in between that token and the 
    next identical token into special_val. This is used to proc after we close

    Exceptions can occur if we encounter and unknown token or a token that is too long
    """
    buffer = ""
    while True:
        try: 
            word = next_tok(gen)
            if word is None:
                break
          
            if '<|' in word or ('<' in word and '|' in next_tok(gen)):
                cur_word = ""
                i = 0
                while i < max_tok_len: # While we are not at the end of token
                    temp = next_tok(gen)
                    if '|>' in temp:
                        break
                    if '|' in temp:
                        next_tok(gen) # Purge '>' token
                        break
                    cur_word += temp
                    i += 1
                if i == max_tok_len:
                    raise Exception("Max token len reached while parsing specials")
                cur_word = clean_tok(cur_word).upper()
                if cur_word in two_piece_toks: # Requires a closing token    
                    if in_special:
                        # Only stop looking for token when we find the right special
                        if cur_word in cur_special: # If the token we just saw is the last token
                            # Are last
                            buffer += proc_special(cur_word, val=special_val)
                            in_special = False
                            cur_special = ""
                            special_val = ""
                            yield buffer
                    else: # We are looking at first tok
                        in_special = True
                        cur_special = clean_tok(cur_word).upper()
                elif cur_word in one_piece_toks: # Only a single toke
                    buffer += proc_special(cur_word)
                    yield buffer
                else: 
                    raise Exception(f"Unknown token: {cur_word}")
                continue

            if in_special:
                special_val += word
                continue
            
            buffer += word
            print(buffer)
            yield buffer
            #buffer += word
        except Exception as e:
            print(e)
            break

@chat.route("/chat_stream", methods=['POST'])
def chat_stream():
    msg_data = request.json.get('message')
    uuid = request.json.get('uuid')
    print(uuid)
    if not msg_data:
        return "Missing 'message' in POST data", 400
    return Response(stream_with_context(chat_tok_generator(msg_data)), mimetype='text/html')

@chat.route("/message/<uuid>", methods=['GET', 'POST'])
def message(uuid: str):
    #message = request.json['message']
    #response = superintend.hoodlem.chat(uuid, message) 
    #return jsonify({"response": response})
    pass

@chat.route("/hoodlem")
def hoodlem():
    if current_user.is_authenticated:
        superintend.core.inform(f"User with username {current_user.username} entered chat with Hoodlem (The speaking module of Superintendent)")
    superintend.core.inform("User entered chat with Hoodlem (The speaking module of Superintendent)")
    chat_uuid = shortuuid.uuid()
    return render_template("hoodlem.html", uuid=chat_uuid)
