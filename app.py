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
            cursor.close()
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
            cursor.close()
            connection.close()
            return redirect("/")
        else:
            cursor.close()
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
        cursor.close()
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
    countries = [
        "", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
        "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
        "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia",
        "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso",
        "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic",
        "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Cote d'Ivoire",
        "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti", "Dominica",
        "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea",
        "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia",
        "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana",
        "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
        "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati",
        "Korea, North", "Korea, South", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon",
        "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi",
        "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico",
        "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar",
        "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria",
        "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea",
        "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda",
        "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino",
        "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore",
        "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka",
        "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand",
        "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu",
        "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan",
        "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
        ]

    gender_options = ["","Male", "Female", "Non-binary", "Other"]

    languages =  [
                    "", "Afrikaans", "Amharic", "Arabic", "Azerbaijani", "Bengali", "Burmese", 
                    "Chinese", "Czech", "Danish", "Dutch", "English", "Finnish", "French", 
                    "German", "Greek", "Hebrew", "Hindi", "Hungarian", "Indonesian", "Italian", 
                    "Japanese", "Kannada", "Korean", "Malay", "Malayalam", "Marathi", "Navajo", 
                    "Nepali", "Norwegian", "Persian", "Polish", "Portuguese", "Punjabi", 
                    "Romanian", "Russian", "Serbian", "Slovak", "Slovenian", "Spanish", 
                    "Swahili", "Swedish", "Tamil", "Telugu", "Thai", "Turkish", "Ukrainian", 
                    "Urdu", "Vietnamese", "Xhosa", "Yoruba", "Zulu", "Other"
                ]

    politics_options = ["","Center", "Left", "Right", "Other"]

    sexualities = ["","Heterosexual", "Homosexual", "Bisexual", "Pansexual", "Asexual", "Other"]

    if request.method == "POST":
        # check valid inputs

        # check age
        age = str(request.form.get("age"))
        try:
            age = int(age)
        except:
            age = None

        if age is not None and age not in range(1, 120):
            flash("Invalid age.")
            return redirect("/profile")
        elif age is None:
            age = "NULL"
        
        # check valid country

        country = str(request.form.get("country"))
        if country not in countries:
            flash("Invalid country.")
            return redirect("/profile")
        if country == "":
            country = "NULL"


        # check gender
        gender = str(request.form.get("gender"))

        if gender not in gender_options:
            flash("No such gender option.")
            return redirect("/profile")
        if gender == "":
            gender = "NULL"

        
        # check sexuality
        sexuality = str(request.form.get("sexuality"))

        if sexuality not in sexualities:
            flash("No such sexuality option.")
            return redirect("/profile")
        if sexuality == "":
            sexuality = "NULL"

        
        # check politics
        politics = str(request.form.get("politics"))

        if politics not in politics_options:
            flash("No such politics option.")
            return redirect("/profile")
        if politics == "":
            politics = "NULL"


        # check language
        native_language = str(request.form.get("language"))

        if native_language not in languages:
            flash("No such language option.")
            return redirect("/profile")
        if native_language == "":
            native_language = "NULL"



        # Connect to the database
        connection = sqlite3.connect("amiwrong.db")
        # Cursor with which to interact with database
        cursor = connection.cursor()

        # update profiles table in database
        cursor.execute("UPDATE profiles SET age = ?, country = ?, gender = ?, sexuality = ?, politics = ?, language = ? WHERE user_id = ?", (age, country, gender, sexuality, politics, native_language, session["user_id"]))

        # commit changes
        connection.commit()
        # close connection
        cursor.close()
        connection.close()


        print("Saved changes to profile")

        # Refresh page
        return redirect("/profile")
    else:
        # Connect to the database
        connection = sqlite3.connect("amiwrong.db")
        # Use Row factory to fetch rows as dictionaries
        connection.row_factory = sqlite3.Row
        # Cursor with which to interact with database
        cursor = connection.cursor()

        # Execute a SELECT query to retrieve a row
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (session["user_id"],))

        # Fetch the row as dict
        row = cursor.fetchone()

        if row:
            age = row['age']
            country = row['country']
            gender = row['gender']
            sexuality = row['sexuality']
            politics = row['politics']
            language = row['language']

        # Close the cursor and connection
        cursor.close()
        connection.close()
        return render_template("profile.html", age=age, country=country, countries=countries, gender=gender, gender_options=gender_options, sexuality=sexuality, sexualities=sexualities, politics=politics, politics_options=politics_options, language=language, languages=languages)


#@login_required