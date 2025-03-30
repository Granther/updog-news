import os
from uuid import uuid4
import random

import shortuuid
import openai
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv
from flask import current_app

from app.models import Story, User
from app.prompts import generate_news_prompt
from app.superintend import gen_interviews, get_superintend
from app import db

superintend = get_superintend()

class Infer():
    def __init__(self):
        load_dotenv()

    def _gen(self, prompt: str, sys_prompt: str, backend=None, model=None, messages=[]):
        model = (model if model else os.getenv('DEFAULT_MODEL'))
        backend = (backend if backend else os.getenv('INFER_BACKEND'))

        if backend == "groq":
            client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        elif backend == "feather":
            client = OpenAI(
                base_url="https://api.featherless.ai/v1",
                api_key=os.getenv('FEATHERLESS_API_KEY')
            )
        else:
            raise RuntimeError(f"Unknown backend, {backend}, specified. Expected 'groq' or 'featherless'")

        # Use messages instead of comment tree
        messages.append(
            {
                "role": "system",
                "content": sys_prompt
            })
        messages.append({
                "role": "user",
                "content": prompt,
            })

        print(messages)

        try:
            chat_comp = client.chat.completions.create(
                messages=messages,
                model=model,
                top_p=float(os.getenv('MODEL_TOP_P', '1.0')),
                temperature=float(os.getenv('MODEL_TEMPERATURE', '1.0')),
                )
        except openai.APIError as e:
            raise RuntimeError(f"Inference exception occured when getting chat completions: {e}")
        except Exception as e:
            raise RuntimeError(f"Unknown exception occured: {e}")
        return chat_comp.choices[0].message.content

    def generate_news(self, title, personality: str=None):
        msg = None

        sys_prompt = generate_news_prompt()

        if personality:
            msg = f"### Title:\n{title}\n### Personality:\n{personality}"
        else:
            msg = f"### Title:\n{title}"
        
        return self._gen(msg, sys_prompt)

_infer = Infer()

def generate_news(title: str, personality: str=None):
    return _infer.generate_news(title, personality)

def write_new_story(app, item: dict):
    with app.app_context():
        try:
            content = generate_news(item['title'], item['personality'])
            story = Story(title=item['title'], content=content, reporter=item['reporter'], catagory=item['catagory'])
            if not superintend.allow_story(story):
                raise Exception("Superintendent denied your story")
            gen_interviews(app, story) # Dispatches new thread in hoodlem
            db.session.add(story)
            db.session.commit()
        except Exception as e:
            raise e

if __name__ == "__main__":
    infer = Infer()
    print(infer._gen("How are you", "You are a helpful AI", "feather"))
