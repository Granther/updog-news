import os

from flask import Flask, session, current_app, g
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_session import Session
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_redis import FlaskRedis

from app.config import DevelopmentConfig, ProductionConfig
from app.logger import create_logger

# Create a single SQLAlchemy instance
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config=DevelopmentConfig):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config.from_object(__name__)

    with app.app_context():
        logger = create_logger(__name__, config)
        current_app.logger = logger
        current_app.bcrypt = Bcrypt(app)
        current_app.redis_client = FlaskRedis(app)

    login_manager.login_view = 'login'
    login_manager.login_message = None
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    # Create all tables if not already created
    db.init_app(app)
    with app.app_context():
        from app.models import Story, Comment, User, Reporter, QueuedStory, QueuedComment
        db.create_all()

    # Imported later to prevent circular import
    from app.routes.main import main

    app.register_blueprint(main)

    return app
