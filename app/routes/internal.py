from flask import Blueprint, abort, render_template, session, jsonify, redirect, url_for, current_app, flash, request
from dotenv import load_dotenv

from app.superintend import SuperIntend, get_superintend

load_dotenv()
superintend = get_superintend()
internal = Blueprint('internal', __name__,
                        template_folder='templates')

@internal.route("/internal")
def internal_index():
    return "Welcom to internal, here are some routes: ..."

@internal.route("/internal/superintend")
def internal_superintend():
    val = ""
    for item in superintend.core.core_messages._get_messages():
        val += f"{item}\n\n"
    return val

