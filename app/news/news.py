from sqlalchemy import text
from sqlalchemy.orm import session
from sqlalchemy.sql import func, desc

from app import db
from app.utils import preserve_markdown, display_catagory
from app.models import Story, User

def get_marquee() -> dict:
    try:
        result = Story.query.order_by(desc(Story.created)).limit(3)
        return {"one": result[0].title, "two": result[1].title, "three": result[2].title}
    except Exception as e:
        return {"one": "-", "two": "-", "three": "-"}

def get_stories(catagory=None) -> list:
    if not catagory: # Select all
        result = Story.query.order_by(desc(Story.created)).all() 
    else:
        result = Story.query.filter_by(catagory=catagory).order_by(desc(Story.created)).all()
    stories = []
    for story in result:
        cat = display_catagory(story.catagory)
        proc_story_content = preserve_markdown(story.title)
        stories.append({"id":story.id, "title":story.title, "content": proc_story_content, "reportername":story.reporter, "catagory": cat})
    return stories

""" Given a story containing <|LINK_SRC|> toks, remove them """
def rm_link_toks(content: str) -> str:
    return content.replace('<|LINK_SRC|>', '')

    
