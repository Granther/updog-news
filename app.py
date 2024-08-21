from flask import Flask, render_template, request, redirect, url_for, flash
from gen_news import GenerateNews, GenerateNewsSQL
from dotenv import load_dotenv
from infer import generate_news
from config import Config
import re
import os

app = Flask(__name__)
app.secret_key = "glorp"
config = Config()
genSQL = GenerateNewsSQL()

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

@app.route("/gen_news")
def gen_news():
    return render_template("gen_news.html")

@app.route("/authors")
def authors():
    return render_template("authors.html")

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
                
    story = generate_news(title=data['title'], prompt=data['guideline'], add_sources=bool(data['sources']))
    if not story:
        msg = "Error generating story, please try again"
        return render_template('gen_news.html', msg=msg) 
    
    genSQL.create_story(title=data['title'], content=story, days=days, author=author, tags=tags)
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template("about.html")

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

if __name__ == "__main__":
    setup_env()
    app.run(debug=True)