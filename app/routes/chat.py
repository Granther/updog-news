import os
from collections import defaultdict
import shortuuid

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
    for word in superintend._groq_chat_stream([{"role": "user", "content": message}]):
        print(word.choices[0].delta.content, end="")
        print("stop")

    print("here now")
    return "wut"

@chat.route("/hoodlem")
def hoodlem():
    if current_user.is_authenticated:
        superintend.core.inform(f"User with username {current_user.username} entered chat with Hoodlem (The speaking module of Superintendent)")
    superintend.core.inform("User entered chat with Hoodlem (The speaking module of Superintendent)")
    chat_uuid = shortuuid.uuid()
    return render_template("hoodlem.html", uuid=chat_uuid)
