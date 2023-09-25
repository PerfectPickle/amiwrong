import os
import sqlite3
import bcrypt

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

from functools import wraps

# Configure application
app = Flask(__name__)
# For session use, which flash requires
app.secret_key = "N0a2FLQ7Qx)ZLf{-4*k6j03EvQ725c=0A"
# set session type
app.config['SESSION_TYPE'] = 'filesystem'

# Custom filters
#app.jinja_env.filters["usd"] = usd

# to use filesystem (instead of signed cookies)
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"

# Ensure templates reload on page refresh when changes have been made
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session
Session(app)

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

def logged_out_required(f):
    """
    Decorator for routes to require that the user is not logged in
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is not None:
            return redirect("/")  # Redirect to a different page if the user is logged in
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    if session.get("user_id") is None:
        return render_template("index.html")
    else:
        return render_template("polls.html")

@app.route("/login", methods=["GET", "POST"])
@logged_out_required
def login():
    if request.method == "POST":
        # get username from form
        username = request.form.get("username")

        # Connect to the database
        connection = sqlite3.connect("amiwrong.db")
        # Cursor with which to interact with database
        cursor = connection.cursor()

        # check if user exists
        user_lookup = cursor.execute("SELECT * FROM users WHERE users.username = ?;", (username,)).fetchall()

        if len(user_lookup) != 1:
            connection.close()
            flash("Username not found")
            return redirect("/login")

        # get password from form
        password = request.form.get("password")
        # get oassword hash from user
        hash = cursor.execute("SELECT hash FROM users WHERE users.username = ?;", (username,)).fetchone()[0]
        print(hash)
        # check inputted password to hash
        if bcrypt.checkpw(password.encode('utf-8'), hash):
            print('Logging in..')
            session["user_id"] = cursor.execute("SELECT id FROM users WHERE users.username = ?;", (username,)).fetchone()[0]
            connection.close()
            return redirect("/")
        else:
            connection.close()
            flash("Incorrect password")
            return redirect("/login")
        print("trinyg to log in")
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
@logged_out_required
def register():
    if request.method == "POST":
        print("register user")
        
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # check username length
        if len(username) < 1:
            flash("Username too short.")
            return redirect("/register")

        # Connect to the database
        connection = sqlite3.connect("amiwrong.db")
        # Cursor with which to interact with database
        cursor = connection.cursor()

        # check username is both unique and valid
        # Query database for username to see if already taken
        username_rows = cursor.execute("SELECT * FROM users WHERE username = ?;", (username,)).fetchall()

        # Ensure username doesn't exist in database already
        if len(username_rows) != 0:
            flash("Sorry, that username is already taken.")
            return redirect("/register")

        # check password length valid
        if len(password) < 8:
            flash("Password must be at least 8 characters long.")
            return redirect("/register")
        elif len(password) > 64:
            flash("Password must be no longer than 64 characters.")
            return redirect("/register")

        # check confirmation matching
        if password != confirmation:
            flash("Password and confirmation were not matching.")
            return redirect("/register")

        # get user ip address
        ip_addr = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

        # generate salt and hash password using bcrypt
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

        
        # create user
        cursor.execute("INSERT INTO users (username, hash, creation_ip) VALUES (?, ?, ?);", (username, password_hash, ip_addr))

        # get user_id for profile creation
        user_id = cursor.execute("SELECT id FROM users WHERE username = ?;", (username,)).fetchone()[0]

        if not str(user_id).isdigit():
            print("Failed to get newly created user_id.")
            connection.close()
            return render_template("register.html", message="Something went wrong.")

        # create profile
        cursor.execute("INSERT INTO profiles (user_id) VALUES (?);", (user_id,))

        # commit changes
        connection.commit()
        # close connection
        connection.close()

        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    # poll creation
    if request.method == "POST":
        return redirect("/")
    else:
        return render_template("create.html")

@app.route("/signout", methods=["GET", "POST"])
@login_required
def signout():
    if request.method == "POST":
        # Forget any user_id
        session.clear()

        # Redirect user to login form
        return redirect("/")
    else:
        return render_template("confirm_signout.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        # TODO save changes to profile
        print("Saved changes to profile")

        # Refresh page
        return redirect("/profile")
    else:
        return render_template("profile.html")


#@login_required