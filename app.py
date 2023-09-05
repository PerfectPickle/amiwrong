import os
import sqlite3

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

from functools import wraps


# Configure application
app = Flask(__name__)

# Custom filters
#app.jinja_env.filters["usd"] = usd

# to use filesystem (instead of signed cookies)
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"

# Ensure templates reload on page refresh when changes have been made
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session
Session(app)

# Connect to the database
connection = sqlite3.connect("gfg.db")
 
# Cursor with which to interact with database
cursor = connection.cursor()

# To execute sqlite3 queries
#cursor.execute()

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def login_required(f):
    """
    Decorator for routes to require login
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("index.html")


connection.close()