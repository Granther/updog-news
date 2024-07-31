from groq import Groq
import xml.etree.ElementTree as ET 
import os

class News:
    def __init__(self, title, prompt, length, content):
        self.title = title
        self.prompt = prompt
        self.content = content
        self.length = length

def parse_news():
    news = []

    for i, file in enumerate(os.listdir('documents')):
        tree = ET.parse(f"documents/{file}")
        root = tree.getroot()

        doc = dict(title=root[0].text, prompt=root[1].text, length=root[2].text, content=root[3].text, idx=i)
        news.append(doc)

    return news






