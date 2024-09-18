from factory import db
from flask_login import UserMixin
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
    username = db.Column(db.String, unique=False, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    containers = db.relationship('Containers', backref='users', lazy=True)

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())

# class Containers(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     created = db.Column(db.TIMESTAMP, nullable=False, server_default=db.func.now())
#     uuid = db.Column(db.String, nullable=True, default=generate_uuid)
#     subdomain = db.Column(db.String, unique=True, nullable=False)
#     srv_id = db.Column(db.String, unique=True, nullable=False)
#     domain = db.Column(db.String, unique=False, nullable=False)
#     port = db.Column(db.Integer, unique=True, nullable=False)
#     rcon_port = db.Column(db.Integer, unique=True, nullable=False)
#     priority = db.Column(db.Integer, unique=False, nullable=True)
#     weight = db.Column(db.Integer, unique=False, nullable=True)
#     priority = db.Column(db.Integer, unique=False, nullable=True)
#     name = db.Column(db.String, unique=False, nullable=False)
#     type = db.Column(db.String, unique=False, nullable=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


