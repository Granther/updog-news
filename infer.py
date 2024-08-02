import openai
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
os.environ["FEATHERLESS_API_KEY"] = os.getenv("FEATHERLESS_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

def generate_news(title, model="NeverSleep/Llama-3-Lumimaid-8B-v0.1"):
    api_key = os.environ.get('FEATHERLESS_API_KEY')
    response = None

    client = OpenAI(
        base_url="https://api.featherless.ai/v1",
        api_key=api_key
    )

    messages=[
        {
            "role": "user",
            "content": f"{title}",
        },
        {
            "role": "system",
            "content": "Roleplay as a news writer. Given a news story title, please generate a fitting news story. Please omit bolding and tokens like **, please break the article into paragraphs"
        }
    ]

    try:
        response = client.chat.completions.create(
            model=model,
            messages= messages,
            temperature=1.0,
            stream=False,
            max_tokens=2000
        )
    except openai.APIError as e:
        print(f"Inference exception occured when getting chat completions: {e}")
        return False

    return response.choices[0].message.content

def perform_search(key: str):
    tavily_client = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
    response = tavily_client.search("Elon musk bought the moon?")

    print(response['results'][1]['url'])  

if __name__ == "__main__":
    perform_search("H")