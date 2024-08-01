from groq import Groq
from openai import OpenAI
import os

def generate_news_groq(title: str):
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Generate a news story for this title: {title}",
                }
            ],
            model="llama3-8b-8192",
        )
    except Exception as e:
        print(f"Exception occured in infer: {e}")

    return chat_completion.choices[0].message.content


def generate_news(title, model="NeverSleep/Llama-3-Lumimaid-8B-v0.1"):
    api_key = os.environ.get('FEATHERLESS_API_KEY')
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
            "content": "Roleplay as a news writer. Given a news story title, please generate a fitting news story. Please omit bolding and tokens like **"
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages= messages,
        temperature=1.0,
        stream=False,
        max_tokens=2000
    )

    return response.choices[0].message.content


