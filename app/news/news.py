from app.utils import preserve_markdown
from app.models import Story, Reporter

def get_marquee() -> dict:
    return {"one": "one", "two": "two", "three": "three"}

def get_stories() -> list:
    result = Story.query.all()
    stories = []
    for story in result:
        reporter = Reporter.query.filter_by(id=story.reporter_id).first()
        proc_story_content = preserve_markdown(story.title)
        stories.append({"id":story.id, "title":story.title, "content": proc_story_content, "uuid":story.uuid, "reportername":reporter.name})
    return stories
