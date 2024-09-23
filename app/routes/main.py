from collections import defaultdict

from flask import Blueprint, abort, render_template, session, jsonify, redirect, url_for, current_app, flash, request
from flask_redis import FlaskRedis
from flask_login import login_required, logout_user, login_user, current_user
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Queue
from uuid import uuid4

from app import db, login_manager
from app.models import Story, Comment, User, Reporter, QueuedStory, QueuedComment
from app.forms import GenerateStoryForm, LoginForm, RegistrationForm, NewReporterForm, CommentForm
from app.queue import queue_story, queue_decide_respond

main = Blueprint('main', __name__,
                        template_folder='templates')

# current_app.logger.info("At index page")

# Submit
#   |
# Make Queue SQL entry
#   |
# Add uuid to queue
#   |
# Call generate up queue time

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = current_app.bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        email = User.query.filter_by(email=form.email.data).first()
        if email:
            flash('Register Unsuccessful. Email already associated with account', 'danger')
            return render_template("register.html", title='Register', form=form)

        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and current_app.bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.index'))
            # next_page = request.args.get('next')
            # return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/')
def index():
    if not session.get("likes", False):
        session['likes'] = []
    stories = []
    result = Story.query.order_by(db.desc(Story.likes)).all()

    for story in result:
        reporter = Reporter.query.filter_by(id=story.reporter_id).first()
        stories.append({"id":story.id, "title":story.title, "content":story.content, "uuid":story.uuid, "reportername":reporter.name, "likes":story.likes})

    return render_template("index.html", stories=stories)

@main.route("/generate",  methods=['GET', 'POST'])
@login_required
def generate():
    form = GenerateStoryForm()

    if form.validate_on_submit():
        uuid = str(uuid4())
        queuedStory = QueuedStory(uuid=uuid, title=form.title.data, guideline=form.guideline.data, user_id=current_user.id, reporter_id=form.reporter_id.data)
        db.session.add(queuedStory)
        db.session.commit()

        queue_story(uuid)

        return redirect(url_for('main.index'))

    return render_template("generate.html", form=form)

@main.route("/new_reporter", methods=['GET', 'POST'])
def new_reporter():
    form = NewReporterForm()

    if form.validate_on_submit():
        uuid = str(uuid4())

        new_reporter = Reporter(uuid=uuid, name=form.name.data, username=form.name.data, personality=form.personality.data)
        db.session.add(new_reporter)
        db.session.commit()

        return jsonify({"id": new_reporter.id})
        # return redirect(url_for('main.index'))
    
    return render_template("new_reporter.html", form=form)

@main.route(f"/story/<uuid>/")
@main.route(f"/story/<uuid>/<title>")
def story(uuid, title=None):
    form = CommentForm()
    results = Story.query.filter_by(uuid=uuid).first()
    comments = Comment.query.filter_by(story_id=results.id).order_by(Comment.created).all()

    def build_comment_tree(comments):
        comment_dict = defaultdict(list)
        top_level_comments = []

        for comment in comments:
            if comment.parent_id:
                comment_dict[comment.parent_id].append(comment)
            else:
                top_level_comments.append(comment)

        return top_level_comments, comment_dict
    
    top_level_comments, comment_tree = build_comment_tree(comments)

    # print(comments, top_level_comments, comment_tree)
    forms = {comment.id: CommentForm() for comment in comments}

    if results:
        reporter = Reporter.query.filter_by(id=results.reporter_id).first()
        story = {"title": results.title, "content": results.content, "reporter_uuid": reporter.uuid, "reporter_name": reporter.name, "reporter_id": results.reporter_id, "uuid": results.uuid}
        return render_template("story.html", **story, form=form, forms=forms, top_level_comments=top_level_comments, comment_tree=comment_tree)

    return render_template("error.html", msg="Story Not Found")

@main.route("/reporters")
def reporters():
    reporters = []
    result = Reporter.query.all()
    for reporter in result:
        reporters.append({"id":reporter.id, "name":reporter.name, "personality":reporter.personality, "uuid":reporter.uuid, "likes":reporter.likes})
    return render_template("reporters.html", reporters=reporters)

@main.route('/about')
def about():
    return render_template("about.html")

@main.route("/comments/<uuid>", methods=['GET', 'POST'])
def comments(uuid):
    if request.method == 'GET':
        results = Story.query.filter_by(uuid=uuid).first()
        comments = Comment.query.filter_by(story_id=results.id).order_by(Comment.created).all()

        def build_comment_tree(comments):
            comment_dict = defaultdict(list)
            top_level_comments = []

            for comment in comments:
                if comment.parent_id:
                    comment_payload = {"id": comment.id, "content": comment.content}
                    comment_dict[comment.parent_id].append(comment_payload)
                else:
                    comment_payload = {"id": comment.id, "content": comment.content}
                    top_level_comments.append(comment_payload)

            return top_level_comments, comment_dict
        
        top_level_comments, comment_tree = build_comment_tree(comments)

        return jsonify({"comment_tree": comment_tree, "top_level_comments": top_level_comments})
    
    return jsonify({"status": False})

@main.route("/comment/<uuid>", methods=['POST', 'GET'])
@login_required
def comment(uuid):
    form = CommentForm()

    if form.validate_on_submit():
        story = Story.query.filter_by(uuid=uuid).first()
        uuid = str(uuid4())

        new_comment = Comment(content=form.comment.data, story_id=story.id, uuid=uuid, user_id=current_user.id)
        db.session.add(new_comment)
        db.session.commit()

        queue_decide_respond(story.uuid, new_comment.uuid)

        return jsonify({"Status": "huh"})

    return jsonify({"Status": "huh"})

@main.route("/reply", methods=['POST', 'GET'])
def reply():
    if request.method == 'POST':
        data = request.get_json()

        parent_id = data.get('parent_id')
        content = data.get('reply')
        story_uuid = data.get('story_id')

        story_id = Story.query.filter_by(uuid=story_uuid).first().id

        print(parent_id, content, story_id)

        uuid = str(uuid4())

        new_reply = Comment(content=content, story_id=story_id, uuid=uuid, user_id=current_user.id, parent_id=parent_id)
        db.session.add(new_reply)
        db.session.commit()

        return jsonify({"status": True})

    #return abort(401)
    return jsonify({"status": False})


@main.route("/test")
def test():
    pass


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

@main.app_template_filter('story_likes')
def story_likes(uuid):
    results = Story.query.filter_by(uuid=uuid).first().likes

    if results:
        return results
    return 0

@main.app_template_filter('story_is_liked')
def story_is_liked(uuid):
    for item in session['likes']:
        if item['uuid'] == uuid:
            return "Liked"
    
    return "Like"

@main.route('/like/<uuid>', methods=['POST'])
def like(uuid):
    likes_history = session['likes']
    for item in likes_history:
        x = item.get('uuid', False)
        if x:
            print("Already liked, unliking and removing from likes list")
            story = Story.query.filter_by(uuid=uuid).first()
            story.likes -= 1
            db.session.add(story)
            db.session.commit()
            likes_history.remove(item)
            return jsonify({"state":"Like", "likes": story.likes})

    print("Not yet liked, adding to likes list and updating row")
    story = Story.query.filter_by(uuid=uuid).first()
    story.likes += 1
    db.session.add(story)
    db.session.commit()
    likes_history.mainend({'uuid': uuid})

    session['likes'] = likes_history

    return jsonify({"state":"Liked", "likes": story.likes})

@main.route(f"/reporter/<uuid>/")
@main.route(f"/reporter/<uuid>/<name>")
def reporter(uuid, name=None):
    results = Reporter.query.filter_by(uuid=uuid).first()
    if results.onetime:
        return redirect(url_for('index'))
    else:
        reporter = {"name":results.name, "personality":results.personality}
        return render_template("reporter.html", **reporter, stories=results.stories)

    return render_template("error.html", msg="Reporter Not Found")
