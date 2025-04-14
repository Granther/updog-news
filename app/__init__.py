import os

from flask import Flask, session, current_app, g
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_session import Session
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from dotenv import load_dotenv

from app.config import DevelopmentConfig, ProductionConfig
from app.logger import create_logger

load_dotenv()

# Create a single SQLAlchemy instance
db = SQLAlchemy()
login_manager = LoginManager()

# Modify your existing code to handle SocketIO properly
def create_socketio_emitter(app):
    """
    Create a function to emit SocketIO events that can be used outside of request context
    
    Args:
        app (Flask): The Flask application instance
    
    Returns:
        function: A function that can safely emit SocketIO events
    """
    def emit_event(event, data):
        with app.app_context():
            try:
                # Use the SocketIO instance from the app config
                socketio = app.extensions['socketio']
                socketio.emit(event, data)
            except Exception as e:
                # Log the error or handle it appropriately
                app.logger.error(f"SocketIO emission error: {e}")
    
    return emit_event

def init_app_extensions(app):
    """
    Initialize application extensions and configure SocketIO
    
    Args:
        app (Flask): The Flask application instance
    
    Returns:
        SocketIO: Configured SocketIO instance
    """
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Store page status in app config
    app.config['page_status'] = {}
    
    # Create and store a custom SocketIO emitter
    app.config['emit_socketio'] = create_socketio_emitter(app)
    
    return socketio

def create_app(config=DevelopmentConfig):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config.from_object(__name__)

    with app.app_context():
        #logger = create_logger(__name__, config)
        #current_app.logger = logger
        current_app.bcrypt = Bcrypt(app)
        current_app.socketio = SocketIO(app)

    socketio = init_app_extensions(app)

    login_manager.login_view = 'main.login'
    login_manager.login_message = None
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    # Create all tables if not already created
    db.init_app(app)
    with app.app_context():
        from app.models import Story, User
        db.create_all()
        # create_defaults(db)

    # Imported later to prevent circular import
    from app.routes.main import main
    from app.routes.chat import chat
    from app.routes.internal import internal

    app.register_blueprint(main)
    app.register_blueprint(chat)
    app.register_blueprint(internal)

    app.extensions['socketio'] = socketio
    
    return app


