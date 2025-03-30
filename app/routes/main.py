import os
import time
from collections import defaultdict
from datetime import datetime

from flask import Blueprint, abort, render_template, session, jsonify, redirect, url_for, current_app, flash, request
from flask_login import login_required, logout_user, login_user, current_user
from flask_socketio import SocketIO, emit
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Queue
from uuid import uuid4   
import shortuuid
from dotenv import load_dotenv

from app import db, login_manager
from app.models import Story, User, Interview
from app.forms import GenerateStoryForm, LoginForm, RegistrationForm, NewReporterForm, CommentForm
from app.utils import preserve_markdown, display_catagory, pretty_timestamp
from app.news import get_marquee, get_stories, write_new_story, rm_link_toks
from app.queue import put_story, start_queue
from app.superintend import SuperIntend, get_superintend

load_dotenv()
#superintend = SuperIntend(os.environ.get("GROQ_API_KEY"), os.environ.get("FEATHERLESS_API_KEY"), os.environ.get("GROQ_API_KEY"))
start_queue()
main = Blueprint('main', __name__,
                        template_folder='templates')

superintend = get_superintend()
content = """
    The White House announced today that First Lady Jill Biden is expecting another grandchild. This news comes as a surprise to many, considering the First Lady is already a grandmother to several grandchildren. Some might even say it's a bit, shall we say, "ripe" for a woman her age.

    The announcement was met with predictable fanfare from the usual suspects. The President, naturally, was ecstatic, gushing about how "thrilled" he was. One can only imagine the political machinations behind this announcement, timed perfectly to distract from, well, let's just say the President's recent... "mishaps."

    The White House, predictably, offered no details about the pregnancy, including the due date or the identity of the expecting parents. They did, however, release a photo of the First Lady beaming, clutching a sonogram picture. Let's be honest, the woman's been through enough with her husband's antics. Maybe she's just trying to find something to smile about.

    Naturally, the media is having a field day with this news. Every outlet is running the same tired stories about "family joy" and "expanding the Biden clan." It's enough to make you wonder if they've ever heard of a story that doesn't involve the Bidens.

    We reached out to a few political analysts for their take on the news. "This is classic Biden," one unnamed source told us, "always looking for a way to control the narrative."

    Another analyst, who wished to remain anonymous, offered a more cynical perspective. "Let's be real," he said, "this is just another way for the White House to distract from the real issues facing the country."

    Whether this is a genuine moment of joy or a carefully orchestrated PR stunt, one thing is certain: the news cycle will be dominated by the impending arrival of another Biden grandchild for the foreseeable future.
    """
#superintend.gen_interview(content)

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
    error = request.args.get('error')
    if error: 
        flash(error, 'danger')
    catagory = request.args.get('catagory')
    if catagory:
        catagory = catagory.lower()

    report_btn = {"text": "Report for Up Dog News", "url": url_for("main.register")}
    if current_user.is_authenticated:
        report_btn = {"text": "Report Now", "url": url_for("main.report")}

    stories = get_stories(catagory=catagory)
    marq = get_marquee()
    return render_template("index.html", stories=stories, marq=marq, report_btn=report_btn)

@main.route("/report", methods=['POST', 'GET'])
@login_required
def report():
    form = GenerateStoryForm()
    if form.validate_on_submit():
        try:
            app = current_app._get_current_object()
            write_new_story(app, {"title": form.title.data, "reporter": form.reporter_name.data, "personality": form.reporter_personality.data, "catagory": form.catagory.data})
            #put_story({"title": form.title.data, "reporter": form.reporter_name.data, "personality": form.reporter_personality.data, "catagory": form.catagory.data, "user_id": current_user.id})
        except Exception as e:
            flash(f'We encountered an error while writing your story, please try again later: {e}', 'danger')
            return redirect(url_for("main.index"))

        flash('UpDog News thanks you for the story, your story will be published in a few moments', 'success')
        return redirect(url_for("main.index"))
    return render_template("report.html", form=form)

@main.route("/interview/<uuid>")
def interview(uuid: str):
    interview = Interview.query.filter_by(uuid=uuid).first()
    if not interview:
        err = f"Interview uuid: {uuid} does not exist"
        logger.fatal(err)
        flash(err)
        return redirect(url_for("error.html"))
    
    return render_template("interview.html", interview=interview)

@main.route("/story/<title>")
@main.route("/story/<category>/<title>")
def story(title, category=None):
    story = Story.query.filter_by(title=title).first()
    if not story:
        # Generate a unique session ID
        session_id = shortuuid.uuid()
        
        # Get the application instance
        app = current_app._get_current_object()
        
        # Ensure page status is initialized
        if 'page_status' not in app.config:
            app.config['page_status'] = {}
        
        # Mark the session as not ready
        app.config['page_status'][session_id] = {
            'ready': False,
            'url': None
        }

        # Start page generation in a background task
        current_app.socketio.start_background_task(
            target=gen_schrod_page, 
            app=app, 
            session_id=session_id, 
            title=title
        )

        return render_template('waiting.html', session_id=session_id)
    else:
        # Existing story rendering logic
        timestamp = pretty_timestamp(story.created)
        read_time = "read time"
        story.catagory = display_catagory(story.catagory)
        #if not story.sources_done: # Not finished async creating sources
        story.content = rm_link_toks(story.content)
        return render_template("story.html", story=story, timestamp=timestamp, read_time=read_time)

def gen_schrod_page(app, session_id: str, title: str):
    """
    Modified page generation function that works with the app factory pattern
    
    Args:
        app (Flask): The Flask application instance
        session_id (str): Unique session identifier
        title (str): Story title
    """
    # Use the emit function created for this app instance
    emit_socketio = app.config.get('emit_socketio')
    error = None

    try:
        reporter, personality, category = superintend.quick_fill(title)
        write_new_story(app, {"title": title, "reporter": reporter, "personality": personality, "catagory": category.lower()})
    except Exception as e:
        error = e

    # Update page status (ensure this uses the app context)
    with app.app_context():
        # Assuming you have a way to access page_status, either globally or through app config
        page_status = current_app.config.get('page_status', {})
        page_status[session_id] = {
            'ready': True,
            'url': f'/story/{title}'
        }
        current_app.config['page_status'] = page_status

    # Emit the event using the custom emitter
    if emit_socketio:
        if error:
            emit_socketio('page_ready', {
                'session_id': session_id,
                'url': f'/?error={error}'
            })
        else:
            emit_socketio('page_ready', {
                'session_id': session_id,
                'url': f'/story/{title}'
            })

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
