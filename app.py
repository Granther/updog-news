from flask import Flask, render_template, request, redirect, url_for, flash
from gen_news import parse_news, create_story
from dotenv import load_dotenv
from infer import generate_news
from config import Config
import re
import os

app = Flask(__name__)
app.secret_key = "glorp"
config = Config()

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
    stories = parse_news()
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
        
        try:
            int(data['days']) 
        except:
            data['days'] = None

        # if any(value == '' for value in data.values()):
        #     msg = "Some feilds empty"
        #     return render_template('gen_news.html', msg=msg)

        # try:
        #     int(data['days'])
        # except:
        #     msg = "Days must take number (0, 1, 2)"
        #     return render_template('gen_news.html', msg=msg)
        
        # else:    
        #     #status = "Generating story, please DONT refresh page. You will be redirected automatically when finished"
        #     #return render_template('gen_news.html', status=status)
        #     pass
        
    story = generate_news(title=data['title'])
    if not story:
        return redirect(url_for('index'))

    create_story(title=data['title'], content=story, days=data['days'], author=data['author'], tag=data['tag'])
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template("about.html")

@app.route(f"/story/<uuid>")
def story(uuid):
    stories = parse_news()
    rend_story = dict()

    for story in stories:
        if story['uuid'] == uuid:
            rend_story = story

    return render_template("story.html", **rend_story)


@app.route("/<title>")
def inline(title):
    title = re.sub('-', ' ', title)

    data = dict(title=title,
                days="0",
                author="Daniel Smith",
                tag="Technology")

    story = generate_news(title=data['title'])
    
    if not story:
        return redirect(url_for('index'))

    uuid = create_story(title=data['title'], content=story, days=data['days'], author=data['author'], tag=data['tag'])

    return redirect(url_for('story', uuid=uuid))

if __name__ == "__main__":
    setup_env()
    app.run(debug=True)