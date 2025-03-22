from sqlalchemy.orm import session
from sqlalchemy.sql import func

from app.utils import preserve_markdown
from app.models import Story, User

def get_marquee() -> dict:
    #result = Story.query.limit(3)
    #print(len(result))
    #total_rows = session.query(func.count(Story.id)).scalar
    #if total_rows < 3:
    #    return {"one": "", "two": "", "three": ""}
    return {"one": "one", "two": "two", "three": "three"}

def get_stories(catagory=None) -> list:
    if not catagory: # Select all
        result = Story.query.all()
    else:
        result = Story.query.filter_by(catagory=catagory).all()
    stories = []
    for story in result:
        reporter = Reporter.query.filter_by(id=story.reporter_id).first()
        proc_story_content = preserve_markdown(story.title)
        stories.append({"id":story.id, "title":story.title, "content": proc_story_content, "uuid":story.uuid, "reportername":reporter.name})
    return stories

    
