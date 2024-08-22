from flask import Flask, render_template, request, redirect, url_for, flash, Response, stream_with_context, jsonify
from gen_news import GenerateNewsSQL
from dotenv import load_dotenv
from infer import Infer
from config import Config
from reporters import ReportersSQL
import re
import os
import json

app = Flask(__name__)
app.secret_key = "glorp"
config = Config()
rep = ReportersSQL()
genSQL = GenerateNewsSQL()
infer = Infer()

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

@app.route('/')
def index():
    stories = genSQL.parse_news()
    return render_template("index.html", stories=stories)

@app.route("/get_reporters", methods=["GET"])
def get_reporters():
    reporters = rep.parse_reporters()
    print(reporters)

    return jsonify(reporters)

@app.route("/gen_news")
def gen_news():
    return render_template("gen_news.html")

@app.route("/reporters")
def reporters():
    reporters = rep.parse_reporters()
    print(reporters)
    return render_template("reporters.html", reporters=reporters)

@app.route("/new_reporter")
def new_reporter():
    return render_template("new_reporter.html")

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
    
    genSQL.create_story(title=finalForm['title'], content=finalForm['story'], days=finalForm['days'], reporter=finalForm['reporter'], tags=finalForm['tags'])

    return redirect(url_for('index'))


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
    json_str = request.args.get('formdata')
    data = json.loads(json_str)

    return Response(stream_with_context(infer.generate_news_stream(title=data['title'], prompt=data['guideline'], reporter=data['reporter'], add_sources=False)), mimetype='text/event-stream')

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

@app.route('/archive')
def archive():
    stories = genSQL.parse_news(index=False)
    return render_template("archive.html", stories=stories)

@app.route('/trash_story/<uuid>')
def trash_story(uuid):
    genSQL.trash(uuid)
    return redirect(url_for('index'))

@app.route("/reporter/<username>")
def reporter(username):
    username = rep.make_username(username)
    reporter = rep.parse_reporters(username=username)[0]
    stories = genSQL.parse_news_reporter(username=username)
    print(reporter)
    print(stories)

    return render_template("reporter.html", **reporter, stories=stories)
if __name__ == "__main__":
    setup_env()
    app.run(debug=True, threaded=True)