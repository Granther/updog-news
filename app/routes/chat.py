import os
from collections import defaultdict
import shortuuid
from queue import Queue

from flask import Blueprint, abort, render_template, session, jsonify, redirect, url_for, current_app, flash, request
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

def proc_special(special: str, val: str=None):
    match special:
        case "KICK":
            print("Going to kick user")
            return

    if val is None:
        raise Exception(f"Token: {special} may expect value, none was passed")

    # 2 Piece token sets
    match special:
        case "GEN_STORY":
            print("Going to generate story: ", val)
            return
    
def next_tok(gen):
    return next(gen).choices[0].delta.content

@chat.route("/chat_stream")
def chat_stream():
 #   with lock:
    json_str = request.args.get('formdata')
    data = json.loads(json_str)
#        return Response(stream_with_context(superintend.chat_with_stream

@chat.route("/message/<uuid>", methods=['GET', 'POST'])
def message(uuid: str):
    message = request.json['message']
    #response = superintend.hoodlem.chat(uuid, message) 
    #return jsonify({"response": response})
    max_tok_len = 10
    buffer = ""
    gen = superintend._groq_chat_stream([{"role": "user", "content": message}])
    cur_special = ""
    special_val = ""
    in_special = False
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
                cur_word = clean_tok(cur_word)
                if cur_word in two_piece_toks: # Requires a closing token    
                    if in_special:
                        # Only stop looking for token when we find the right special
                        if cur_word in cur_special: # If the token we just saw is the last token
                            # Are last
                            proc_special(cur_word, val=special_val)
                            in_special = False
                            cur_special = ""
                            special_val = ""
                    else: # We are looking at first tok
                        in_special = True
                        cur_special = clean_tok(cur_word)
                elif cur_word in one_piece_toks: # Only a single toke
                    proc_special(cur_word)
                else: 
                    raise Exception(f"Unknown token: {cur_word}")
                continue

            if in_special:
                special_val += word
                continue

            buffer += word
        except Exception as e:
            print(e)
            break
    print(buffer)
    return "wut"

@chat.route("/hoodlem")
def hoodlem():
    if current_user.is_authenticated:
        superintend.core.inform(f"User with username {current_user.username} entered chat with Hoodlem (The speaking module of Superintendent)")
    superintend.core.inform("User entered chat with Hoodlem (The speaking module of Superintendent)")
    chat_uuid = shortuuid.uuid()
    return render_template("hoodlem.html", uuid=chat_uuid)
