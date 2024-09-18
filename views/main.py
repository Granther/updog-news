from flask import Blueprint, render_template, session

from models import User, Reporter, Article, Comment

main = Blueprint('main', __name__,
                        template_folder='templates')

@main.route('/')
def index():
    if not session.get("likes", False):
        session['likes'] = []
    stories = []
    result = Article.query.order_by(db.desc(Article.likes)).all()
    for story in result:
        reporter = Reporter.query.filter_by(id=story.reporter_id).first()
        stories.append({"id":story.id, "title":story.title, "content":story.content, "uuid":story.uuid, "reportername":reporter.name, "likes":story.likes})

    return render_template("index.html", stories=stories)