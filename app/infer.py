import os
from uuid import uuid4

import openai
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv
from flask import current_app

from app import db, rq
from app.models import Story, QueuedStory, QueuedComment

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

    def generate_news(self, title, guideline: str=None, model="NeverSleep/Llama-3-Lumimaid-8B-v0.1", add_sources=False):
        response = None

        client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key=os.getenv('FEATHERLESS_API_KEY')
        )

        msg = None

        if guideline:
            msg = f"### Title:\n{title}\n### Guideline:\n{guideline}"
        else:
            msg = f"### Title:\n{title}"
        
        sys_prompt = "Roleplay as a news writer. Given a news story title and some snippet of information to include, please generate a fitting news story. Please omit bolding and tokens like **, please break the article into paragraphs" 

        messages=[
            {
                "role": "user",
                "content": f"{msg}",
            },
            {
                "role": "system",
                "content": sys_prompt
            }
        ]

        try:
            response = client.chat.completions.create(
                model=model,
                messages= messages,
                temperature=1.0,
                stream=False,
                max_tokens=int(os.getenv("MAX_TOKENS", "3000"))
            )
        except openai.APIError as e:
            print(f"Inference exception occured when getting chat completions: {e}")
            return False


        return response.choices[0].message.content


_infer = Infer()

def generate_news(title: str, guideline: str=None, model: str="NeverSleep/Llama-3-Lumimaid-8B-v0.1", add_sources: bool=False):
    return _infer.generate_news(title, guideline, model, add_sources)

@rq.job
def generate(uuid: str):
    return _infer.generate(uuid)

if __name__ == "__main__":
    # os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    # os.environ["FEATHERLESS_API_KEY"] = os.getenv("FEATHERLESS_API_KEY")
    # os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
    pass

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