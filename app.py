from flask import Flask, render_template

app = Flask(__name__)

links = [
    {"name": "Google", "url": "google.com"},
    {"name": "Google", "url": "google.com"}    
]

@app.route('/')
def index():
    return render_template("index.html", links=links)

@app.route('/about')
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
