from flask import Flask, render_template, request, redirect, url_for, flash
from gen_news import GenerateNews
from dotenv import load_dotenv
from infer import generate_news
from config import Config
import re
import os

app = Flask(__name__)
app.secret_key = "glorp"
config = Config()
generate = GenerateNews(config)

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
    stories = generate.parse_news(config.documents_path)
    return render_template("index.html", stories=stories)

@app.route("/gen_news")
def gen_news():
    return render_template("gen_news.html")

@app.route('/read_form', methods=['POST'])
def read_form():
    msg = None
    status = None

    if request.method == "POST":
        data = request.form
        if not data:
            msg = "Error recieving form data"
            return render_template('gen_news.html', msg=msg)
        
        if data['title'] == '': # If no title
            msg = "Title feild must be filled"
            return render_template('gen_news.html', msg=msg)
        
        try:
            if data['days'] != '':
                int(data['days'])
        except ValueError:
            msg = "Days Old field must be a number"
            return render_template('gen_news.html', msg=msg)
        
    story = generate_news(title=data['title'], prompt=data['guideline'])
    if not story:
        msg = "Error generating story, please try again"
        return render_template('gen_news.html', msg=msg) 
    
    generate.create_story(title=data['title'], content=story, days=data['days'], author=data['author'], tag=data['tag'], prompt=data['guideline'])
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/control/<uuid>')
def control(uuid):
    return render_template('control.html', uuid=uuid)

@app.route("/toggle_archive/<uuid>")
def toggle_archive(uuid):
    generate.toggle_archive(uuid)
    return redirect(url_for('index'))

@app.route(f"/story/<uuid>")
def story(uuid):
    stories = generate.parse_all_news()
    rend_story = dict()

    for story in stories:
        if story['uuid'] == uuid:
            return render_template("story.html", **story)
    
    return render_template("error.html", msg="Story Not Found")

@app.route(f"/archived_story/<uuid>")
def archived_story(uuid):
    stories = generate.parse_news(config.archive_path)
    rend_story = dict()

    for story in stories:
        if story['uuid'] == uuid:
            return render_template("story.html", **story)
    
    return render_template("error.html", msg="Story Not Found")

@app.route('/archive')
def archive():
    stories = generate.parse_news(config.archive_path)
    return render_template("archive.html", stories=stories)


@app.route('/trash_story/<uuid>')
def trash_story(uuid):
    generate.trash(uuid)
    return redirect(url_for('index'))

# @app.route("/<title>")
# def inline(title):
#     title = re.sub('-', ' ', title)

#     story = generate_news(title=title)
    
#     if not story:
#         return redirect(url_for('index'))

#     uuid = generate.create_story(title=title, content=story)

#     return redirect(url_for('story', uuid=uuid))

if __name__ == "__main__":
    setup_env()
    app.run(debug=True)