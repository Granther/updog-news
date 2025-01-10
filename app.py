from flask import Flask, render_template, request, redirect, url_for, flash, Response, stream_with_context, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from sqlalchemy.orm import DeclarativeBase
from gen_news import GenerateNewsSQL
from flask_session import Session
from dotenv import load_dotenv
from infer import Infer
from config import Config
from reporters import ReportersSQL
import shortuuid
import re
import os
import json
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///updog.db'
app.config['SECRET_KEY'] = 'glorp'
db = SQLAlchemy(app)
SESSION_TYPE = "filesystem"
app.config.from_object(__name__)
Session(app)

def gen_uuid():
    return str(shortuuid.uuid())

class Reporters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    name = db.Column(db.String(100), nullable=False)
    uuid = db.Column(db.String, nullable=True, unique=True, default=gen_uuid)
    personality = db.Column(db.String, nullable=False)
    trashed = db.Column(db.Boolean, nullable=True, default=False)    
    archived = db.Column(db.Boolean, nullable=True, default=False)
    stories = db.relationship('Stories', backref='reporters', lazy=True)

class Stories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    title = db.Column(db.String, nullable=False)
    uuid = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    trashed = db.Column(db.Boolean, nullable=True, default=False)    
    archived = db.Column(db.Boolean, nullable=True, default=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey('reporters.id'), nullable=False)

class ReporterCreationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    personality = TextAreaField('Personality', validators=[DataRequired()])
    submit = SubmitField('Generate')

# Actually creates the database in ./instances, prob should only run in debug
with app.app_context():
    db.create_all()

config = Config()
rep = ReportersSQL()
genSQL = GenerateNewsSQL()
infer = Infer()
lock = threading.Lock()

queue = []

def setup_env():
    try:
        load_dotenv()
        os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
        os.environ["FEATHERLESS_API_KEY"] = os.getenv("FEATHERLESS_API_KEY")
        os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

    except EnvironmentError:
        print("Environment data is missing")
        raise RuntimeError
    except Exception as e:
        print(f"Exception {e} occured when preparing evironment")

def fix_stories(stories: list):
    for story in stories:
        story['content'] = story['content'][:150].replace("<br>", "")

    return stories

def check_default_reporter():
    results = Reporters.query.filter_by(id=1).first()
    if not results:
        default = Reporters(name="Default", personality="Default", uuid="Default")
        db.session.add(default)
        db.session.commit()

@app.route('/')
def index():
    if not session.get("likes", False):
        session['likes'] = []
    stories = []
    # result = Stories.query.order_by(db.desc(Stories.likes)).all()
    # for story in result:
    #     reporter = Reporters.query.filter_by(id=story.reporter_id).first()
    #     stories.append({"id":story.id, "title":story.title, "content":story.content, "uuid":story.uuid, "reportername":reporter.name, "likes":story.likes})

    return render_template("index.html", stories=stories)

@app.route("/get_reporters", methods=["GET"])
def get_reporters():
    reporters = rep.parse_reporters()

    return jsonify(reporters)

@app.route("/gen_news",  methods=['GET', 'POST'])
def gen_news():
    return render_template("gen_news.html")

@app.route("/reporters")
def reporters():
    reporters = []
    result = Reporters.query.all()
    for reporter in result:
        reporters.append({"id":reporter.id, "name":reporter.name, "personality":reporter.personality, "uuid":reporter.uuid, "likes":reporter.likes})
    return render_template("reporters.html", reporters=reporters)

@app.route("/new_reporter", methods=['GET', 'POST'])
def new_reporter():
    form = ReporterCreationForm()
    if form.validate_on_submit():
        reporter = Reporters(name=form.name.data, personality=form.personality.data, onetime=False)
        db.session.add(reporter)
        db.session.commit()
        return redirect(url_for('reporters'))
    return render_template('new_reporter.html', form=form)

@app.route("/create_reporter", methods=["POST"])
def create_reporter():
    if request.method == "POST":
        data = request.form
        if not data:
            msg = "Error recieving form data"
            return render_template('new_reporter.html', msg=msg)
        
        if data['name'] == '': # If no title
            msg = "Name field must be filled"
            return render_template('new_reporter.html', msg=msg)
        
        if data['personality'] == '': # If no personality
            msg = "Personality field must be filled"
            return render_template('new_reporter.html', msg=msg)

    res = rep.create_reporter(name=data['name'], personality=data['personality'], bio=data['bio'])

    return redirect(url_for("reporters"))

@app.route('/post', methods=['POST'])
def post():
    finalForm = request.get_json()['story']
    reporter_name = finalForm.get('reporter', False)
    if not reporter_name:
        raise RuntimeError("Cannot get reporter from form")
    
    reporter = Reporters.query.filter_by(name=reporter_name, onetime=False).first()
    if not reporter:
        new_onetime = Reporters(name=reporter_name, onetime=True, personality="Default")
        db.session.add(new_onetime)
        db.session.commit()
        reporter_id = new_onetime.id
    else:
        reporter_id = reporter.id

    story = Stories(title=finalForm['title'], content=finalForm['story'], reporter_id=reporter_id, uuid=str(shortuuid.uuid()))
    db.session.add(story)
    db.session.commit()
    return jsonify({"status":"good"})


@app.route('/read_form', methods=['POST'])
def read_form():
    msg = None

    if request.method == "POST":
        data = request.form
        if not data:
            msg = "Error recieving form data"
            return render_template('gen_news.html', msg=msg)
        
        if data['title'] == '': # If no title
            msg = "Title field must be filled"
            return render_template('gen_news.html', msg=msg)
        
        try:
            if data['days'] != '':
                int(data['days'])
        except ValueError:
            msg = "Days Old field must be a number"
            return render_template('gen_news.html', msg=msg)
        
    if data['days'] == '':
        days = config.def_days_old
    if data['author'] == '':
        author = config.def_author
    if data['tags'] == '':
        tags = config.def_tag
                
    story = infer.generate_news(title=data['title'], prompt=data['guideline'], add_sources=bool(data['sources']))
    if not story:
        msg = "Error generating story, please try again"
        return render_template('gen_news.html', msg=msg) 
    
    genSQL.create_story(title=data['title'], content=story, days=days, author=author, tags=tags)
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template("about.html")

@app.route("/queue", methods=['POST', 'GET'])
def queue():
    print("Added to queue")

@app.route("/stream")
def stream():
    json_str = request.args.get('formdata')
    data = json.loads(json_str)
    return Response(stream_with_context(infer.generate_news_stream_groq(title=data['title'], prompt=data['guideline'], reporter=data['reporter'], add_sources=False)), mimetype='text/event-stream')

@app.route('/control/<uuid>')
def control(uuid):
    return render_template('control.html', uuid=uuid)

@app.route("/toggle_archive/<uuid>")
def toggle_archive(uuid):
    genSQL.toggle_archive(uuid)
    return redirect(url_for('index'))

@app.template_filter('get_name')
def get_name(id):
    results = Reporters.query.filter_by(id=id).first().name
    return results

@app.template_filter('story_likes')
def story_likes(uuid):
    results = Stories.query.filter_by(uuid=uuid).first().likes

    if results:
        return results
    return 0

@app.template_filter('story_is_liked')
def story_is_liked(uuid):
    for item in session['likes']:
        if item['uuid'] == uuid:
            return "Liked"
    
    return "Like"

@app.route('/like/<uuid>', methods=['POST'])
def like(uuid):
    likes_history = session['likes']
    for item in likes_history:
        x = item.get('uuid', False)
        if x:
            print("Already liked, unliking and removing from likes list")
            story = Stories.query.filter_by(uuid=uuid).first()
            story.likes -= 1
            db.session.add(story)
            db.session.commit()
            likes_history.remove(item)
            return jsonify({"state":"Like", "likes": story.likes})

    print("Not yet liked, adding to likes list and updating row")
    story = Stories.query.filter_by(uuid=uuid).first()
    story.likes += 1
    db.session.add(story)
    db.session.commit()
    likes_history.append({'uuid': uuid})

    session['likes'] = likes_history

    return jsonify({"state":"Liked", "likes": story.likes})

@app.route(f"/reporter/<uuid>/")
@app.route(f"/reporter/<uuid>/<name>")
def reporter(uuid, name=None):
    results = Reporters.query.filter_by(uuid=uuid).first()
    if results.onetime:
        return redirect(url_for('index'))
    else:
        reporter = {"name":results.name, "personality":results.personality}
        return render_template("reporter.html", **reporter, stories=results.stories)

    return render_template("error.html", msg="Reporter Not Found")

@app.route(f"/story/<uuid>/")
@app.route(f"/story/<uuid>/<title>")
def story(uuid, title=None):
    results = Stories.query.filter_by(uuid=uuid).first()
    if results:
        reporter = Reporters.query.filter_by(id=results.reporter_id).first()
        story = {"title": results.title, "content": results.content, "reporter_uuid": reporter.uuid, "reporter_name": reporter.name, "reporter_id": results.reporter_id, "uuid": results.uuid}
        return render_template("story.html", **story)

    return render_template("error.html", msg="Story Not Found")

if __name__ == "__main__":
    setup_env()
    app.run(debug=True)