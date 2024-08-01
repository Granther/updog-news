import openai
from openai import OpenAI
import os

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

    return response.choices[0].message.content


