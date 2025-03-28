import os
import inspect
from datetime import datetime
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

def pretty_timestamp(created) -> str:
        dif = datetime.utcnow() - created
        seconds = dif.total_seconds()
        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{int(minutes)} minutes ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{int(hours)} hours ago"
        elif seconds < 604800:
            days = seconds // 86400
            return f"{int(days)} days ago"
        else:
            weeks = seconds // 604800
            return f"{int(weeks)} weeks ago"
