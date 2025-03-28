from sqlalchemy import text
from sqlalchemy.orm import session
from sqlalchemy.sql import func

from app import db
from app.utils import preserve_markdown, display_catagory
from app.models import Story, User

def get_marquee() -> dict:
    try:
        result = session.query(Story).order_by(Story.id.desc()).limit(3).all()
#        query = text("SELECT TOP 3 FROM Story")
#        result = session.query(query)
        #for i in result:
         #   print(i)
        print("here")
    except Exception as e:
        print(e)
        return {"one": "one", "two": "two", "three": "three"}

def get_stories(catagory=None) -> list:
    if not catagory: # Select all
        result = Story.query.all()
    else:
        result = Story.query.filter_by(catagory=catagory).all()
    stories = []
    for story in result:
        #reporter = Reporter.query.filter_by(id=story.reporter_id).first()
        cat = display_catagory(story.catagory)
        proc_story_content = preserve_markdown(story.title)
        stories.append({"id":story.id, "title":story.title, "content": proc_story_content, "reportername":story.reporter, "catagory": cat})
    return stories

""" Given a story containing <|LINK_SRC|> toks, remove them """
def rm_link_toks(content: str) -> str:
    return content.replace('<|LINK_SRC|>', '')

    
