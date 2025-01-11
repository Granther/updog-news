import os
from uuid import uuid4
import random

import openai
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv
from flask import current_app

from app import db, rq
from app.models import Story, QueuedStory, QueuedComment, Reporter, Comment
from app.utils import get_reply_tree, whoami, account_type_owns
from app.prompts import decide_respond_prompt, respond_comment_prompt, generate_news_prompt

class Infer():
    def __init__(self):
        load_dotenv()

    def generate(self, uuid: str):
        queued_story = QueuedStory.query.filter_by(uuid=uuid).first()
        queued_comment = QueuedComment.query.filter_by(uuid=uuid).first()

        if queued_story:
            generated_story = self.generate_news(title=queued_story.title, guideline=queued_story.guideline)
            story = Story(uuid=uuid, content=generated_story, title=queued_story.title, guideline=queued_story.guideline, user_id=queued_story.user_id, reporter_id=queued_story.reporter_id)
            db.session.add(story)

        elif queued_comment:
            # generated_comment = self.generate_comment(title=queued_story.title, guideline=queued_story.guideline)
            # story = Story(uuid=uuid, content=generated_story, title=queued_story.title, guideline=queued_story.guideline, user_id=queued_story.user_id, reporter_id=queued_story.reporter_id)
            # db.session.add(story)
            pass

        else:
            raise RuntimeError(f"Exception occured when attempting to generate from queue, uuid {uuid} not found")

        db.session.commit()

    def decide_respond(self, story_uuid: str, comment_uuid: str) -> bool:
        reply_tree = get_reply_tree(comment_uuid)
        story = Story.query.filter_by(uuid=story_uuid).first()
        reporter = Reporter.query.filter_by(id=story.reporter_id).first()
        original_comment = Comment.query.filter_by(uuid=comment_uuid).first()

        if not original_comment.parent_id:
            current_app.logger.debug(f"{whoami()}:::Comment is a top level comment")
        else:
            current_app.logger.debug(f"{whoami()}:::Comment is a reply to another comment")
            parent_to_original = Comment.query.filter_by(id=original_comment.parent_id).first()

            """ 
            The parent of the comment that a user replied to, initiating this reply generation
            If this parent's reporter is this' reporter, it is valid
            """
            if parent_to_original.reporter != reporter:
                current_app.logger.debug(f"{whoami()}:::Cannot reply to comment for which this reporter is not in the chain of")
                return False


        sys_prompt = decide_respond_prompt(name=reporter.name, personality=reporter.personality) 

        prompt = f"### Original Post/Story:\n{story.content}\n### Comment/Comment Tree:\n{reply_tree}\n"

        response = self._gen(prompt, sys_prompt)
        if "no" in response.lower():
            current_app.logger.debug(f"decide_respond ::: Responding with choice of {False}")
            return False
        elif "yes" in response.lower():
            current_app.logger.debug(f"decide_respond ::: Responding with choice of {True}")
            return True
        else:
            choice = random.choice([True, False]) 
            current_app.logger.debug(f"decide_respond ::: Responding with random choice of {choice}")
            return choice

    def respond_comment(self, story_uuid: str, comment_uuid: str):
        # Use semantic analysis to decide 
        # Chance to respond to top level
        # Always respond to threaded comments

        reply_tree = get_reply_tree(comment_uuid)
        story = Story.query.filter_by(uuid=story_uuid).first()
        reporter = Reporter.query.filter_by(id=story.reporter_id).first()

        sys_prompt = respond_comment_prompt(name=reporter.name, personality=reporter.personality)

        prompt = f"### Original Post/Story:\n{story.content}\n### Comment/Comment Tree, you are responding to the most recent one:\n{reply_tree}\n"

        original_comment = Comment.query.filter_by(uuid=comment_uuid).first()
        comment_content = self._gen(prompt, sys_prompt)
        uuid = str(uuid4())

        new_comment = Comment(content=comment_content, story_id=story.id, uuid=uuid, user_id=original_comment.user_id, parent_id=original_comment.id)
        db.session.add(new_comment)
        db.session.commit()

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

    def generate_news(self, title, guideline: str=None):
        msg = None

        sys_prompt = generate_news_prompt()

        if guideline:
            msg = f"### Title:\n{title}\n### Guideline:\n{guideline}"
        else:
            msg = f"### Title:\n{title}"
        
        return self._gen(msg, sys_prompt)

_infer = Infer()

def generate_news(title: str, guideline: str=None):
    return _infer.generate_news(title, guideline)

@rq.job
def generate(uuid: str):
    return _infer.generate(uuid)

@rq.job
def respond_comment(story_uuid: str, comment_uuid: str):
    return _infer.respond_comment(story_uuid, comment_uuid)

@rq.job
def decide_respond(story_uuid: str, comment_uuid: str):
    return _infer.decide_respond(story_uuid, comment_uuid)

if __name__ == "__main__":
    # os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    # os.environ["FEATHERLESS_API_KEY"] = os.getenv("FEATHERLESS_API_KEY")
    # os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
    infer = Infer()
    print(infer._gen("How are you", "You are a helpful AI", "feather"))

# perform_search("Donald trump is a dog", n_results=3)
# from tavily import TavilyClient
# def perform_search(self, search: str, n_results=1):
#     tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
#     response = tavily_client.search(search, max_results=n_results)

#     urls = list()
#     for res in response['results']:
#         urls.append(res['url'])

#     return urls

# if add_sources:
#     try:
#         sources = self.perform_search(title)
#     except:
#         print("Failure to retrieve sources.. skipping")

#     sys_prompt = """Roleplay as a news writer. Given a news story title and some snippet of information to include, please generate a fitting news story. Please cite many fake articles, use the token {source} when referencing the source. 

#     Example: 
#     "Donald trump touched me" ({source}), she said
#     "Meteors were raining from the sky" ({source})    

#     Please omit bolding and tokens like **, also omit the title as well, please break the article into paragraphs"""
