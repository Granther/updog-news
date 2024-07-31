from flask import Flask, render_template, request
from gen_news import parse_news

app = Flask(__name__)

links = [
    {"name": "Google", "url": "google.com"},
    {"name": "Google", "url": "google.com"}    
]

stories = parse_news()

@app.route('/')
def index():
    return render_template("index.html", stories=stories)

@app.route('/read_form', methods=['POST'])
def read_form():
    data = request.form 
  
    return { 
        'title' : data['title'], 
        'prompt': data['prompt'], 
    } 

@app.route('/about')
def about():
    return render_template("about.html")

@app.route("/gen_news")
def gen_news():
    return render_template("gen_news.html")

@app.route(f"/story/<int:idx>")
def story(idx):
    rend_story = stories[idx]
    return render_template("story.html", **rend_story)


if __name__ == "__main__":
    app.run(debug=True)
