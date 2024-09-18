from flask import Blueprint, render_template, session, jsonify, redirect, url_for
from flask_redis import FlaskRedis

from app import db
from app.models import Story, Comment, User, Reporter, QueuedStory, QueuedComment
from app.forms import GenerateStoryForm

main = Blueprint('main', __name__,
                        template_folder='templates')

from rq import Queue
from redis import Redis
 
redis_conn = Redis()
 
q = Queue(connection=redis_conn)
 
result = q.enqueue(print, 'http://nvie.com')

@main.route('/')
def index():
    if not session.get("likes", False):
        session['likes'] = []
    stories = []
    result = Story.query.order_by(db.desc(Story.likes)).all()
    for story in result:
        reporter = Reporter.query.filter_by(id=story.reporter_id).first()
        stories.mainend({"id":story.id, "title":story.title, "content":story.content, "uuid":story.uuid, "reportername":reporter.name, "likes":story.likes})

    return render_template("index.html", stories=stories)


@main.route("/generate",  methods=['GET', 'POST'])
def generate():
    form = GenerateStoryForm()

    if form.validate_on_submit():
        print(form.title.data)
        return redirect(url_for('main.index'))

    return render_template("generate.html", form=form)

@main.route(f"/story/<uuid>/")
@main.route(f"/story/<uuid>/<title>")
def story(uuid, title=None):
    results = Story.query.filter_by(uuid=uuid).first()
    if results:
        reporter = Reporter.query.filter_by(id=results.reporter_id).first()
        story = {"title": results.title, "content": results.content, "reporter_uuid": reporter.uuid, "reporter_name": reporter.name, "reporter_id": results.reporter_id, "uuid": results.uuid}
        return render_template("story.html", **story)

    return render_template("error.html", msg="Story Not Found")

@main.route("/reporters")
def reporters():
    reporters = []
    result = Reporter.query.all()
    for reporter in result:
        reporters.mainend({"id":reporter.id, "name":reporter.name, "personality":reporter.personality, "uuid":reporter.uuid, "likes":reporter.likes})
    return render_template("reporters.html", reporters=reporters)

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

# @main.template_filter('story_likes')
# def story_likes(uuid):
#     results = Stories.query.filter_by(uuid=uuid).first().likes

#     if results:
#         return results
#     return 0

# @main.template_filter('story_is_liked')
# def story_is_liked(uuid):
#     for item in session['likes']:
#         if item['uuid'] == uuid:
#             return "Liked"
    
#     return "Like"

# @main.route('/like/<uuid>', methods=['POST'])
# def like(uuid):
#     likes_history = session['likes']
#     for item in likes_history:
#         x = item.get('uuid', False)
#         if x:
#             print("Already liked, unliking and removing from likes list")
#             story = Stories.query.filter_by(uuid=uuid).first()
#             story.likes -= 1
#             db.session.add(story)
#             db.session.commit()
#             likes_history.remove(item)
#             return jsonify({"state":"Like", "likes": story.likes})

#     print("Not yet liked, adding to likes list and updating row")
#     story = Stories.query.filter_by(uuid=uuid).first()
#     story.likes += 1
#     db.session.add(story)
#     db.session.commit()
#     likes_history.mainend({'uuid': uuid})

#     session['likes'] = likes_history

#     return jsonify({"state":"Liked", "likes": story.likes})

# @main.route(f"/reporter/<uuid>/")
# @main.route(f"/reporter/<uuid>/<name>")
# def reporter(uuid, name=None):
#     results = Reporters.query.filter_by(uuid=uuid).first()
#     if results.onetime:
#         return redirect(url_for('index'))
#     else:
#         reporter = {"name":results.name, "personality":results.personality}
#         return render_template("reporter.html", **reporter, stories=results.stories)

#     return render_template("error.html", msg="Reporter Not Found")
