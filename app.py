from flask import Flask, render_template, request, redirect, url_for
from gen_news import parse_news, create_story
from dotenv import load_dotenv
from infer import generate_news
import os

load_dotenv()
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

app = Flask(__name__)

stories = parse_news()

@app.route('/')
def index():
    stories = parse_news()
    return render_template("index.html", stories=stories)

@app.route('/read_form', methods=['POST'])
def read_form():
    data = request.form 

    story = generate_news(title=data['title'])
    create_story(title=data['title'], content=story, days=data['days'])

    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template("about.html")

@app.route("/gen_news")
def gen_news():
    return render_template("gen_news.html")

@app.route(f"/story/<uuid>")
def story(uuid):
    rend_story = dict()

    for story in stories:
        if story['uuid'] == uuid:
            print("found rend story")
            rend_story = story

    return render_template("story.html", **rend_story)


if __name__ == "__main__":
    app.run(debug=True)