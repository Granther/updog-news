from app import db
from flask_login import UserMixin

class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    #uuid = db.Column(db.String, unique=True, nullable=False)
    title = db.Column(db.String, unique=True, nullable=False)
    content = db.Column(db.String, unique=False, nullable=False)
#    guideline = db.Column(db.String, unique=False, nullable=True)
    reporter = db.Column(db.String, unique=False, nullable=False)
    catagory = db.Column(db.String, unique=False, nullable=True)
#    trashed = db.Column(db.Boolean, nullable=True, default=False)    
#    archived = db.Column(db.Boolean, nullable=True, default=False)
#    likes = db.Column(db.Integer, nullable=True, default=0)
#    comments = db.relationship('Comment', backref='story')
#    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#    reporter_id = db.Column(db.Integer, db.ForeignKey('reporter.id'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    username = db.Column(db.String, unique=True, nullable=False)
    # email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    # stories = db.relationship('Story', backref='user')
#    comments = db.relationship('Comment', backref='user')
#    liked_stories = db.relationship('Story', backref='user')

'''
class QueuedStory(db.Model):
    """Pre-Generated story waiting on execution queue"""

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    uuid = db.Column(db.String, unique=True, nullable=False)
    title = db.Column(db.String, unique=False, nullable=False)
    guideline = db.Column(db.String, unique=False, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reporter_id = db.Column(db.Integer, db.ForeignKey('reporter.id'))

class QueuedComment(db.Model):
    """Pre-Generated comment waiting on execution queue"""

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    uuid = db.Column(db.String, unique=True, nullable=False)
    # title = db.Column(db.String, unique=False, nullable=False)
    # guideline = db.Column(db.String, unique=False, nullable=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # reporter_id = db.Column(db.Integer, db.ForeignKey('reporter.id'))

# class Comment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
#     content = db.Column(db.String, unique=False, nullable=False)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
#     story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
#     likes = db.Column(db.Integer, nullable=True, default=0)
#     parent = db.Column(db.Integer, db.ForeignKey('comment.id'))
#     child = db.relationship('Comment', backref='comment')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    uuid = db.Column(db.String, unique=True, nullable=False)
    content = db.Column(db.String, unique=False, nullable=False)

    # Both are nullable because they are mutually exclusive, cannot be owned by user and reporter
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('reporter.id'), nullable=True)
    username = db.Column(db.String, unique=False, nullable=False)

    story_id = db.Column(db.Integer, db.ForeignKey('story.id'))
    # likes = db.Column(db.Integer, nullable=True, default=0)
    # parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    # children = db.relationship('Comment', backref=db.backref('parent_comment', remote_side=[id]), lazy='dynamic')
    
    # When querying a comment, I can access the user object with *.user.*. Requires relationship in User model as well
    # user = db.relationship('User', back_populates='comments')


class Reporter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    uuid = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)
    username = db.Column(db.String, unique=False, nullable=False)
    personality = db.Column(db.String, unique=False, nullable=False)
    trashed = db.Column(db.Boolean, nullable=True, default=False)    
    archived = db.Column(db.Boolean, nullable=True, default=False)
    likes = db.Column(db.Integer, nullable=True, default=0)
    stories = db.relationship('Story', backref='reporter')
    comments = db.relationship('Comment', backref='reporter')
'''
