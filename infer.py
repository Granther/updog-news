import openai
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv
from config import Config
from uuid import uuid4
import os
import time
import re
import html

config = Config()

class Infer():
    def __init__(self):
        pass

    def generate_news(self, title, prompt: str=None, model="NeverSleep/Llama-3-Lumimaid-8B-v0.1", add_sources=False):
        api_key = os.environ.get('FEATHERLESS_API_KEY')
        response = None

        client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key=api_key
        )

        msg = None
        sources = None

        if prompt:
            msg = f"### Title:\n{title}\n### Guideline:\n{prompt}"
        else:
            msg = f"### Title:\n{title}"

        if add_sources:
            try:
                sources = self.perform_search(title)
            except:
                print("Failure to retrieve sources.. skipping")

            sys_prompt = """Roleplay as a news writer. Given a news story title and some snippet of information to include, please generate a fitting news story. Please cite many fake articles, use the token {source} when referencing the source. 

            Example: 
            "Donald trump touched me" ({source}), she said
            "Meteors were raining from the sky" ({source})    

            Please omit bolding and tokens like **, also omit the title as well, please break the article into paragraphs"""

        else:
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
                max_tokens=int(config.max_tokens)
            )
        except openai.APIError as e:
            print(f"Inference exception occured when getting chat completions: {e}")
            return False

        return response.choices[0].message.content + f"\n\n {sources}"

    def generate_news_stream(self, title, prompt: str=None, model="NeverSleep/Llama-3-Lumimaid-8B-v0.1", add_sources=False):
        api_key = os.environ.get('FEATHERLESS_API_KEY')
        response = None

        client = OpenAI(
            base_url="https://api.featherless.ai/v1",
            api_key=api_key
        )

        msg = None

        if prompt:
            msg = f"### Title:\n{title}\n### Guideline:\n{prompt}"
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

        response = client.chat.completions.create(
            model=model,
            messages= messages,
            temperature=1.0,
            stream=True,
            max_tokens=int(config.max_tokens)
        )

        uuid = str(uuid4())
        self.partial_message = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                self.partial_message = self.partial_message + chunk.choices[0].delta.content
                # Some kind of encoding error occurs in the SSE, this fixes it
                self.partial_message = self.partial_message.replace('\n', '<br>').replace('\r', '<br>')
                yield f"data: {self.partial_message} uuid: {uuid}\n\n"


    def perform_search(self, search: str, n_results=1):
        tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
        response = tavily_client.search(search, max_results=n_results)

        urls = list()
        for res in response['results']:
            urls.append(res['url'])

        return urls

if __name__ == "__main__":
    load_dotenv()
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    os.environ["FEATHERLESS_API_KEY"] = os.getenv("FEATHERLESS_API_KEY")
    os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

    # perform_search("Donald trump is a dog", n_results=3)