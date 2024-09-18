import re
import os
import json
import threading

from flask import Flask, render_template, request, redirect, url_for, flash, Response, stream_with_context, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_session import Session
from dotenv import load_dotenv

from gen_news import GenerateNewsSQL
from infer import Infer
from reporters import ReportersSQL
from config import DevelopmentConfig, ProductionConfig

from app.routes.main import main

# Create a single SQLAlchemy instance
db = SQLAlchemy()

def create_app(config=DevelopmentConfig):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URI
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config.from_object(__name__)

    Session(app)

    # Create all tables if not already created
    with app.app_context():
        db.create_all()

    app.register_blueprint(main)

    return app
