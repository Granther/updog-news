import os
import inspect
from collections import defaultdict
from markupsafe import Markup
import markdown

from app import db

def whoami():
    return inspect.stack()[1][3]

def preserve_markdown(s):
    html = markdown.markdown(s)
    html.replace('\n', '<br>')
    return Markup(html)

def display_catagory(catagory: str) -> str:
    catagories = {
    "world": "World",
    "technology": "Technology",
    "politics": "Politics",
    "other": "Other",
    "business": "Business",
    }
    return catagories[catagory]
