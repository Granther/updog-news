from flask import Flask, render_template, request, redirect, url_for, flash, Response, stream_with_context, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_session import Session

# from gen_news import GenerateNewsSQL
# from infer import Infer
# from reporters import ReportersSQL
from app.config import DevelopmentConfig, ProductionConfig

# Create a single SQLAlchemy instance
db = SQLAlchemy()

def create_app(config=DevelopmentConfig):
    

def build_app(config=DevelopmentConfig):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config.from_object(__name__)

    print(config.DATABASE_URI)

    # SESSION_TYPE = 'filesystem'
    # Session(app)

    # Create all tables if not already created
    db.init_app(app)
    with app.app_context():
        from app.models import Story, Comment, User, Reporter, QueuedStory, QueuedComment
        db.create_all()

    # Imported later to prevent circular import
    from app.routes.main import main

    app.register_blueprint(main)

    return app
