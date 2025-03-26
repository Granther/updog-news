import os
from collections import defaultdict

from flask import Blueprint, abort, render_template, session, jsonify, redirect, url_for, current_app, flash, request
from flask_login import login_required, logout_user, login_user, current_user
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Queue
from uuid import uuid4   
from dotenv import load_dotenv

from app import db, login_manager
from app.models import Story, User
from app.forms import GenerateStoryForm, LoginForm, RegistrationForm, NewReporterForm, CommentForm
from app.utils import preserve_markdown, display_catagory
from app.news import get_marquee, get_stories, write_new_story
from app.queue import put_story, start_queue
from app.superintend import SuperIntend

load_dotenv()
#superintend = SuperIntend(os.environ.get("GROQ_API_KEY"), os.environ.get("FEATHERLESS_API_KEY"), os.environ.get("GROQ_API_KEY"))
start_queue()
main = Blueprint('main', __name__,
                        template_folder='templates')
#superintend.chat("What is my name", 2)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = current_app.bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            flash('Register Unsuccessful. Username already registered', 'danger')
            return render_template("register.html", title='Register', form=form)

        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and current_app.bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/')
def index():
    catagory = request.args.get('catagory')
    if catagory:
        catagory = catagory.lower()

    report_btn = {"text": "Report for Up Dog News", "url": url_for("main.register")}
    if current_user.is_authenticated:
        report_btn = {"text": "Report Now", "url": url_for("main.report")}

    stories = get_stories(catagory=catagory)
    marq = get_marquee()
    return render_template("index.html", stories=stories, marq=marq, report_btn=report_btn)

'''
@main.route("/generate",  methods=['GET', 'POST'])
def generate():
    form = GenerateStoryForm()
    reporters = Reporter.query.all()
    form.reporters.choices = [f"{reporter.name} | {reporter.personality}" for reporter in reporters]
    # form.reporters.choices = [(reporter.name, reporter.personality) for reporter in reporters]

    if form.validate_on_submit():
        uuid = str(uuid4())
        reporter_name = form.reporters.data.split(" |")[0]
        reporter_id = Reporter.query.filter_by(name=reporter_name).first().id
        # print(f"Reporter: {form.reporters.data}")
        queuedStory = QueuedStory(uuid=uuid, title=form.title.data, guideline=form.guideline.data, reporter_id=reporter_id)
        db.session.add(queuedStory)
        db.session.commit()

        queue_story(uuid)

        return redirect(url_for('main.index'))

    return render_template("generate.html", form=form)
'''

@main.route("/report", methods=['POST', 'GET'])
@login_required
def report():
    form = GenerateStoryForm()
    if form.validate_on_submit():
        try:
            write_new_story({"title": form.title.data, "reporter": form.reporter_name.data, "personality": form.reporter_personality.data, "catagory": form.catagory.data})
            #put_story({"title": form.title.data, "reporter": form.reporter_name.data, "personality": form.reporter_personality.data, "catagory": form.catagory.data, "user_id": current_user.id})
        except Exception as e:
            flash(f'We encountered an error while writing your story, please try again later: {e}', 'danger')
            return redirect(url_for("main.index"))

        flash('UpDog News thanks you for the story, your story will be published in a few moments', 'success')
        return redirect(url_for("main.index"))
    return render_template("report.html", form=form)


@main.route("/story/<uuid>/")
@main.route("/story/<uuid>/<title>")
def story(uuid, title=None):
    story = Story.query.filter_by(uuid=uuid).first()
    timestamp = "test"
    read_time = "read time"
    story.catagory = display_catagory(story.catagory)
    #story.content = "<h1>Hello</h1><br><br><p>test</p>"
    return render_template("story.html", story=story, timestamp=timestamp, read_time=read_time)

#    form = CommentForm()
#    results = Story.query.filter_by(uuid=uuid).first()
#    comments = Comment.query.filter_by(story_id=results.id).order_by(Comment.created).all()

    # print(comments, top_level_comments, comment_tree)
#    forms = {comment.id: CommentForm() for comment in comments}
#    comments = [{"username": comment.username, "text": comment.content} for comment in comments]

#    if results:
#        reporter = Reporter.query.filter_by(id=results.reporter_id).first()
#        proc_story_content = preserve_markdown(results.content)
        # comments = [{"username": "Gronk", "text": "I bonked"}]
#        story = {"title": results.title, "content": proc_story_content, "reporter_uuid": reporter.uuid, "reporter_name": reporter.name, "reporter_id": results.reporter_id, "uuid": results.uuid}
#        return render_template("story1.html", **story, comments=comments, form=form, forms=forms, logged_in=current_user.is_authenticated)

@main.route('/about')
def about():
    return render_template("about.html")


# @main.route("/get_reporters", methods=["GET"])
# def get_reporters():
#     reporters = rep.parse_reporters()

#     return jsonify(reporters)

# @main.route("/new_reporter", methods=['GET', 'POST'])
# def new_reporter():
#     form = ReporterCreationForm()
#     if form.validate_on_submit():
#         reporter = Reporters(name=form.name.data, personality=form.personality.data, onetime=False)
#         db.session.add(reporter)
#         db.session.commit()
#         return redirect(url_for('reporters'))
#     return render_template('new_reporter.html', form=form)

# @main.route("/create_reporter", methods=["POST"])
# def create_reporter():
#     if request.method == "POST":
#         data = request.form
#         if not data:
#             msg = "Error recieving form data"
#             return render_template('new_reporter.html', msg=msg)
        
#         if data['name'] == '': # If no title
#             msg = "Name field must be filled"
#             return render_template('new_reporter.html', msg=msg)
        
#         if data['personality'] == '': # If no personality
#             msg = "Personality field must be filled"
#             return render_template('new_reporter.html', msg=msg)

#     res = rep.create_reporter(name=data['name'], personality=data['personality'], bio=data['bio'])

#     return redirect(url_for("reporters"))

# @main.route('/post', methods=['POST'])
# def post():
#     finalForm = request.get_json()['story']
#     reporter_name = finalForm.get('reporter', False)
#     if not reporter_name:
#         raise RuntimeError("Cannot get reporter from form")
    
#     reporter = Reporters.query.filter_by(name=reporter_name, onetime=False).first()
#     if not reporter:
#         new_onetime = Reporters(name=reporter_name, onetime=True, personality="Default")
#         db.session.add(new_onetime)
#         db.session.commit()
#         reporter_id = new_onetime.id
#     else:
#         reporter_id = reporter.id

#     story = Stories(title=finalForm['title'], content=finalForm['story'], reporter_id=reporter_id, uuid=str(shortuuid.uuid()))
#     db.session.add(story)
#     db.session.commit()
#     return jsonify({"status":"good"})


# @main.route('/read_form', methods=['POST'])
# def read_form():
#     msg = None

#     if request.method == "POST":
#         data = request.form
#         if not data:
#             msg = "Error recieving form data"
#             return render_template('gen_news.html', msg=msg)
        
#         if data['title'] == '': # If no title
#             msg = "Title field must be filled"
#             return render_template('gen_news.html', msg=msg)
        
#         try:
#             if data['days'] != '':
#                 int(data['days'])
#         except ValueError:
#             msg = "Days Old field must be a number"
#             return render_template('gen_news.html', msg=msg)
        
#     if data['days'] == '':
#         days = config.def_days_old
#     if data['author'] == '':
#         author = config.def_author
#     if data['tags'] == '':
#         tags = config.def_tag
                
#     story = infer.generate_news(title=data['title'], prompt=data['guideline'], add_sources=bool(data['sources']))
#     if not story:
#         msg = "Error generating story, please try again"
#         return render_template('gen_news.html', msg=msg) 
    
#     genSQL.create_story(title=data['title'], content=story, days=days, author=author, tags=tags)
#     return redirect(url_for('index'))

# @main.route("/queue", methods=['POST', 'GET'])
# def queue():
#     print("Added to queue")

# @main.route("/stream")
# def stream():
#     json_str = request.args.get('formdata')
#     data = json.loads(json_str)
#     return Response(stream_with_context(infer.generate_news_stream_groq(title=data['title'], prompt=data['guideline'], reporter=data['reporter'], add_sources=False)), mimetype='text/event-stream')

# @main.route('/control/<uuid>')
# def control(uuid):
#     return render_template('control.html', uuid=uuid)

# @main.route("/toggle_archive/<uuid>")
# def toggle_archive(uuid):
#     genSQL.toggle_archive(uuid)
#     return redirect(url_for('index'))

# @main.template_filter('get_name')
# def get_name(id):
#     results = Reporters.query.filter_by(id=id).first().name
#     return results

# likes_history = session['likes']
# for item in likes_history:liked
#     x = item.get('uuid', False)
#     if x:
#         print("Already liked, unliking and removing from likes list")
#         story = Story.query.filter_by(uuid=uuid).first()
#         story.likes -= 1
#         db.session.add(story)
#         db.session.commit()
#         likes_history.remove(item)
#         return jsonify({"state":"Like", "likes": story.likes})

# print("Not yet liked, adding to likes list and updating row")
# story = Story.query.filter_by(uuid=uuid).first()
# story.likes += 1
# db.session.add(story)
# db.session.commit()
# likes_history.mainend({'uuid': uuid})

# session['likes'] = likes_history

# return jsonify({"state":"Liked", "likes": story.likes})
