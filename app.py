from flask import Flask, render_template, request, redirect, url_for, flash, Response, stream_with_context, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from sqlalchemy.orm import DeclarativeBase
from gen_news import GenerateNewsSQL
from dotenv import load_dotenv
from infer import Infer
from config import Config
from reporters import ReportersSQL
import re
import os
import json
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///updog.db'
app.config['SECRET_KEY'] = 'glorp'
db = SQLAlchemy(app)

class Reporters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    name = db.Column(db.String(100), nullable=False)
    personality = db.Column(db.String, nullable=False)
    trashed = db.Column(db.Boolean, nullable=True, default=False)    
    archived = db.Column(db.Boolean, nullable=True, default=False)
    likes = db.Column(db.Integer, nullable=True, default=0)
    stories = db.relationship('Stories', backref='reporters', lazy=True)

class Stories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    trashed = db.Column(db.Boolean, nullable=True, default=False)    
    archived = db.Column(db.Boolean, nullable=True, default=False)
    likes = db.Column(db.Integer, nullable=True, default=0)
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

    if os.path.isfile("database.db"):
        print("Database exists")
    elif not os.path.isfile("database.db"):
        try:
            import sqlite3
            connection = sqlite3.connect('database.db')
            with open('schema.sql') as f:
                connection.executescript(f.read())
            cur = connection.cursor()
            cur.execute("INSERT INTO posts (title, content) VALUES (?, ?)",
                        ('First Post', 'Content for the first post')
                        )
            connection.commit()
            connection.close()
            print("Created DB")
        except:
            pass

def fix_stories(stories: list):
    for story in stories:
        story['content'] = story['content'][:150].replace("<br>", "")

    return stories

@app.route('/')
def index():
    stories = fix_stories(genSQL.parse_news())
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
    reporters = rep.parse_reporters()
    reporters = []
    x = Reporters.query.all()
    for reporter in x:
        reporters.append({"id":reporter.id, "name":reporter.name, "personality":reporter.personality})
    return render_template("reporters.html", reporters=reporters)

@app.route("/new_reporter", methods=['GET', 'POST'])
def new_reporter():
    form = ReporterCreationForm()
    if form.validate_on_submit():
        reporter = Reporters(name=form.name.data, personality=form.personality.data)
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
    #story = Stories(title=finalForm['title'], content=finalForm['content'])
    res = genSQL.create_story(title=finalForm['title'], content=finalForm['story'], days=finalForm['days'], reporter=finalForm['reporter'], tags=finalForm['tags'])

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

@app.route("/stream")
def stream():
    with lock:
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

@app.route(f"/story/<uuid>")
def story(uuid):
    stories = genSQL.parse_news(all=True)

    for story in stories:
        if story['uuid'] == uuid:
            return render_template("story.html", **story)
    
    return render_template("error.html", msg="Story Not Found")

# @app.route('/archive')
# def archive():
#     stories = fix_stories(genSQL.parse_news(index=False))
#     return render_template("archive.html", stories=stories)

# @app.route('/trash_story/<uuid>')
# def trash_story(uuid):
#     genSQL.trash(uuid)
#     return redirect(url_for('index'))

@app.route("/reporter/<id>")
def reporter(id):
    results = Reporters.query.filter_by(id=id).first()
    reporter = {"name":results.name, "personality":results.personality}

    return render_template("reporter.html", **reporter, stories=results.stories)

if __name__ == "__main__":
    setup_env()
    app.run(debug=True)