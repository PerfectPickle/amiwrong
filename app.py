import os
import sqlite3
import bcrypt
import random
import string

from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session

from functools import wraps

import random
import string
from datetime import datetime, timedelta

### Global variables

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

###

def generate_unique_id(length=11):
    characters = string.ascii_letters + string.digits + '-_'
    return ''.join(random.choice(characters) for i in range(length))

# custom dict factory to use inplace of Sqlite3 Row object
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

# get poll and answers and vote count (TESTING ONLY) from db
def get_poll(unique_id):
    connection = sqlite3.connect("amiwrong.db")
    # Use Row factory to fetch rows as dictionaries
    connection.row_factory = dict_factory

    cursor = connection.cursor()
    poll = cursor.execute("SELECT * FROM polls WHERE unique_id=?;", (unique_id,)).fetchone()
    my_poll_dict = {}
    list_of_answer_dicts = cursor.execute("SELECT * FROM answers WHERE poll_id=?;", (poll["id"],)).fetchall()
    choices = []
    for a in list_of_answer_dicts:
        choices.append(a["answer"])
    poll["choices"] = choices

    list_of_demo_questions = cursor.execute("SELECT * FROM demographics_options WHERE poll_id=?;", (poll["id"],)).fetchall()
    preset_demo_questions = {}
    custom_demographics = []
    for demo_dict in list_of_demo_questions:
        # if preset, add to preset dict, else add to custom demo list
        if str(demo_dict["demographic"]).lower() in ["age", "country", "gender", "sexuality", "language", "politics"]:
            demo_values = []
            match str(demo_dict["demographic"]).lower():
                case "age":
                    preset_demo_questions["Age"] = [0, 1, 2, 3, 4]
                case "country":
                    preset_demo_questions["Country"] = countries
                case "gender":
                    preset_demo_questions["Gender"] = gender_options
                case "sexuality":
                    preset_demo_questions["Sexuality"] = sexualities
                case "politics":
                    preset_demo_questions["Politics"] = politics_options
                case "language":
                    preset_demo_questions["Language"] = languages
                case _:
                    print(f'Error matching preset demographics for {str(demo_dict["demographic"]).lower()}')
        else:
            custom_demographics.append(str(demo_dict["demographic"]))

    poll["demographics"] = preset_demo_questions
    poll["custom_demographics"] = custom_demographics

    cursor.close()
    connection.close()
    
    return poll

# get user profile demographic answers from db as dict, if not found, returns False
def get_profile(user_id):
    connection = sqlite3.connect("amiwrong.db")
    # use row factory to fetch rows as dictionaries
    connection.row_factory = dict_factory
    cursor = connection.cursor()

    try:
        profile = cursor.execute("SELECT * FROM profiles WHERE user_id=?;", (user_id,)).fetchone()
        try:
            age = int(profile.get("age"))
            if age <= 0 or age > 120:
                raise Exception("No valid age in profile")
            profile["age"] = age
        except:
            profile["age"] = ""
    except:
        profile = False
    
    cursor.close()
    connection.close()

    return profile


# get vote counts, optionally limited to a list of demographics
def get_vote_count(unique_id, demographics=None):
    # validate input
    if not unique_id or (demographics is not None and not isinstance(demographics, dict)):
        raise ValueError("Invalid unique_id or demographics argument")

    try:
        connection = sqlite3.connect("amiwrong.db")
        cursor = connection.cursor()

        # retrieve poll_id using unique_id
        poll_id = cursor.execute("SELECT id FROM polls WHERE unique_id=?;", (unique_id,)).fetchone()
        if poll_id is None:
            raise ValueError(f"No poll found with unique_id {unique_id}")
        poll_id = poll_id[0]

        votes = {}

        # get list of answer options for the poll
        answers = cursor.execute("SELECT id, answer FROM answers WHERE poll_id=?;", (poll_id,)).fetchall()
        for answer_id, answer_text in answers:
            if demographics:
                params = [poll_id, answer_id]
                demographic_subqueries = []

                for i, (demo, value) in enumerate(demographics.items(), start=1):
                    print(demo, value)

                    # do a separate query for when no value is given, i.e., nonresponse
                    if value == "":
                        demographic_subquery = f"""
                        AND NOT EXISTS (
                            SELECT 1
                            FROM demographics_responses dr{i}
                            INNER JOIN votes v ON dr{i}.vote_id = v.id
                            INNER JOIN demographics_options do{i} ON dr{i}.demographic_option_id = do{i}.id
                            WHERE v.poll_id = ?
                            AND v.chosen_answer_id = ?
                            AND do{i}.poll_id = v.poll_id
                            AND do{i}.demographic = ?
                        )
                        """
                        demographic_subqueries.append(demographic_subquery)
                        params.extend([poll_id, answer_id, demo])
                    elif demo.lower() == "age":
                        age_range_start = int(value[:-1])
                        print(age_range_start)
                        age_range_end = age_range_start + 10
                        demographic_subquery = f"""
                            AND do{i}.poll_id = v.poll_id
                            AND do{i}.demographic LIKE ?
                            AND CAST(dr{i}.demographic_response AS INTEGER) >= ? 
                            AND CAST(dr{i}.demographic_response AS INTEGER) < ?
                        """
                        demographic_subqueries.append(demographic_subquery)
                        params.extend([demo, age_range_start, age_range_end])
                    else:
                        demographic_subquery = f"""
                            AND do{i}.poll_id = v.poll_id
                            AND do{i}.demographic = ?
                            AND dr{i}.demographic_response = ?
                        """
                        demographic_subqueries.append(demographic_subquery)
                        params.extend([demo, value])

                demographic_filter = " ".join(demographic_subqueries)
                vote_count_query = f"""
                    SELECT COUNT(DISTINCT v.id) AS unique_votes_count
                    FROM votes v
                    {' '.join([f'JOIN demographics_responses dr{i} ON v.id = dr{i}.vote_id' for i in range(1, len(demographics)+1)])}
                    {' '.join([f'JOIN demographics_options do{i} ON dr{i}.demographic_option_id = do{i}.id' for i in range(1, len(demographics)+1)])}
                    WHERE v.poll_id = ? 
                    AND v.chosen_answer_id = ? 
                    {demographic_filter};
                """
            else:
                vote_count_query = "SELECT COUNT(*) FROM votes WHERE poll_id=? AND chosen_answer_id=?;"
                params = (poll_id, answer_id)

            print(vote_count_query)
            print(params)
            vote_count = cursor.execute(vote_count_query, params).fetchone()[0]
            print(f'vote count: {vote_count}')
            votes[answer_text] = vote_count

    except sqlite3.Error as e:
        print(f"An error occurred: {e.args[0]}")
        votes = {}
    finally:
        # Ensure the cursor and the database connection are closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return votes

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
        connection = sqlite3.connect("amiwrong.db")
        # Use Row factory to fetch rows as dictionaries
        connection.row_factory = dict_factory

        cursor = connection.cursor()
        polls = cursor.execute("SELECT * FROM polls WHERE user_id=?;", (session.get("user_id"),)).fetchall()
    
        return render_template("polls.html", polls=polls)

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

        # log user in
        session["user_id"] = user_id

        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    # poll creation
    if request.method == "POST":
        # check user hasn't exceeded poll creation limit / constraint. This is an anti-spam measure
        max_polls_per_day = 3

        # Connect to the database
        connection = sqlite3.connect("amiwrong.db")
        # Cursor with which to interact with database
        cursor = connection.cursor()

        # calculate the datetime 24 hours ago from now
        twenty_four_hours_ago = datetime.now() - timedelta(days=1)
        # format it so it's compat with sqlite
        formatted_time = twenty_four_hours_ago.strftime('%Y-%m-%d %H:%M:%S')

        user_polls_made_in_last_day = cursor.execute("""
            SELECT COUNT(*)
            FROM polls
            WHERE user_id = ?
            AND creation_date > ?
        """, (session["user_id"], formatted_time)).fetchone()[0]

        if user_polls_made_in_last_day >= max_polls_per_day:
            flash('24 hour poll creation limit ({}) reached.'.format(max_polls_per_day))
            # close connection
            cursor.close()
            connection.close()
            return redirect("/create")

        # get form inputs
        question = request.form.get("pollQuestion")
        assumption = request.form.get("pollAssumption")
        if len(assumption.strip()) <= 0:
            assumption = "NULL"

        poll_choices = []
        i = 1
        while f"choice{i}" in request.form:
            choice = request.form.get(f"choice{i}")
            if choice:  # to prevent empty choices from being added
                poll_choices.append(choice)
            i += 1

        
        demographic_options = request.form.getlist('demographicOptions')

        i = 1
        while f"customDemo{i}" in request.form:
            demo = request.form.get(f"customDemo{i}")
            if demo:  # to prevent empty custom demographics from being added
                demographic_options.append(demo)
            i += 1


        # check question length
        if len(question) <= 3:
            flash("Question too short.")
            # close connection
            cursor.close()
            connection.close()
            return redirect("/create")

        # confirm at least 2 nonempty options
        choice_counter = 0
        choices = []
        for choice in poll_choices:
            if len(choice) > 0:
                choices.append(choice)
        
        if len(choices) < 2:
            flash("You must specify at least 2 choices.")
            # close connection
            cursor.close()
            connection.close()
            return redirect("/create")

        # save to database
        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            try:
                cursor.execute("BEGIN TRANSACTION;") # to prevent concurrency issues especially with cursor.lastrowid
                cursor.execute("INSERT INTO polls (user_id, unique_id, question, assumption) VALUES (?, ?, ?, ?);", (session["user_id"], generate_unique_id(), question, assumption))
                poll_id = cursor.lastrowid
                for choice in choices:
                    cursor.execute("INSERT INTO answers (poll_id, answer) VALUES (?, ?);", (poll_id, choice))
                for demo in demographic_options:
                    cursor.execute("INSERT INTO demographics_options (poll_id, demographic) VALUES (?, ?);", (poll_id, demo))


                connection.commit() # commit transaction
                break
            except sqlite3.IntegrityError:
                connection.rollback() # rollback / cancel transaction
                retry_count += 1
            except Exception as e:
                connection.rollback()
                print(f"Error: {e}")  # or you can use logging
                break

        if retry_count == max_retries:
            print("Max retries reached. Poll creation failed.")  # Handle this situation, e.g., by returning an error message to the user

        cursor.close()
        connection.close()

        return redirect("/")
    else:
        demographics = ["Age", "Country", "Gender", "Sexuality", "Politics", "Language"]
        max_choices = 20
        max_custom_demo_options = 3 
        return render_template("create.html", demographics=demographics, max_choices=max_choices, max_custom_demo_options=max_custom_demo_options)


@app.route("/poll/<unique_id>", methods=["GET", "POST"])
def view_poll(unique_id):
    poll = get_poll(unique_id)
    print(unique_id)
    if not poll:
        abort(404) 

    if request.method == "POST":
        # check valid answer
        poll_answer = request.form.get("pollChoice")
        if poll_answer not in poll["choices"]:
            flash("Invalid answer")
            return redirect(f'/poll/{unique_id}')

        poll_answer_id = get_answer_id(poll_answer, poll["id"])

        # check valid demographic input
        demo_answers = {}
        for d in poll["demographics"].keys():
            demo_answers[d] = request.form.get(d)
            # check that preset demographic category and answer is valid
            match str(d).lower():
                case "age":
                    try:
                        if int(demo_answers[d]) <= 0 or int(demo_answers[d]) >= 130:
                            flash("Invalid age entered")
                            return redirect(f'/poll/{unique_id}')
                    except:
                        flash("Invalid age entered")
                        return redirect(f'/poll/{unique_id}')
                case "country":
                    if demo_answers[d] not in countries:
                        flash("Invalid demographic data submitted")
                        return redirect(f'/poll/{unique_id}')
                case "gender":
                    if demo_answers[d] not in gender_options:
                        flash("Invalid demographic data submitted")
                        return redirect(f'/poll/{unique_id}')
                case "sexuality":
                    if demo_answers[d] not in sexualities:
                        flash("Invalid demographic data submitted")
                        return redirect(f'/poll/{unique_id}')
                case "politics":
                    if demo_answers[d] not in politics_options:
                        flash("Invalid demographic data submitted")
                        return redirect(f'/poll/{unique_id}')
                case "language":
                    if demo_answers[d] not in languages:
                        flash("Invalid demographic data submitted")
                        return redirect(f'/poll/{unique_id}')
                case _:
                    flash("Invalid demographic category submitted")
                    return redirect(f'/poll/{unique_id}')
            if demo_answers[d] == "":
                demo_answers.pop(d, None)  # remove nonresponse

        for d in poll["custom_demographics"]:
            demo_answer = request.form.get(d)
            if demo_answer:
                demo_answers[d] = demo_answer
            else:
                demo_answers.pop(d, None)  # remove nonresponse

        # save vote to db
        connection = sqlite3.connect("amiwrong.db")
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO votes (user_id, poll_id, chosen_answer_id) VALUES (?, ?, ?)",
                           (session["user_id"], poll["id"], poll_answer_id))
            vote_id = cursor.lastrowid

            # Insert demographic responses
            for demographic, response in demo_answers.items():
                demographic_option_id = get_demographic_option_id(demographic, poll["id"])
                if demographic_option_id is not None:
                    cursor.execute("INSERT INTO demographics_responses (vote_id, demographic_option_id, demographic_response) VALUES (?, ?, ?)",
                                   (vote_id, demographic_option_id, response))

            connection.commit()
        except sqlite3.Error as e:
            connection.rollback()
            flash("An error occurred while saving your vote.")
            return redirect(f'/poll/{unique_id}')
        finally:
            cursor.close()
            connection.close()

        return redirect(f'/poll/{unique_id}')
    else:
        votes = get_vote_count(unique_id)
        # if user is not logged in, show poll results
        if 'user_id' not in session:
            return render_template('poll_results.html', poll=poll, votes=votes)

        # if user is logged in, check if they have voted on this poll and get their choice
        connection = sqlite3.connect("amiwrong.db")
        cursor = connection.cursor()
        vote_check = cursor.execute("SELECT COUNT(*) FROM votes WHERE user_id = ? AND poll_id = ?", (session["user_id"], poll["id"])).fetchone()[0]
        if vote_check > 0:
            user_choice = cursor.execute(""" 
                SELECT answers.answer 
                FROM votes 
                JOIN answers ON votes.chosen_answer_id = answers.id 
                JOIN polls ON votes.poll_id = polls.id 
                WHERE votes.user_id = ? AND polls.unique_id = ?;
                """, (session["user_id"], unique_id)).fetchone()[0]
        else:
            user_choice = None
        cursor.close()
        connection.close()

        # get user profile
        profile = get_profile(session["user_id"])

        # if the user has voted, display the poll results, else render poll taking page
        if vote_check > 0:
            return render_template('poll_results.html', poll=poll, votes=votes, user_choice=user_choice)
        else:
            print(poll)
            return render_template('poll.html', poll=poll, profile=profile)

# helper function to get demographic_option_id
def get_demographic_option_id(demographic, poll_id):
    connection = sqlite3.connect("amiwrong.db")
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM demographics_options WHERE demographic = ? AND poll_id = ?", (demographic, poll_id,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result[0] if result else None

# helper function to get answer_id of an option for a poll
def get_answer_id(answer, poll_id):
    connection = sqlite3.connect("amiwrong.db")
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM answers WHERE answer = ? AND poll_id = ?", (answer, poll_id))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    return result[0] if result else None


@app.route('/get_filtered_votes')
def get_filtered_votes():
    poll_id = request.args.get('poll_id')
    demographics = request.args.get('demographics')  # this would be a string in the format of 'gender:male,age:30-40'
    
    # convert demographics string to dictionary
    demographic_filters = {}
    if demographics:
        for demographic in demographics.split(','):
            key, value = demographic.split(':')
            demographic_filters[key] = value
    
    votes = get_vote_count(poll_id, demographic_filters)
    
    return jsonify(votes)


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
        profile = get_profile(session["user_id"])

        if profile:
            age = profile['age']
            country = profile['country']
            gender = profile['gender']
            sexuality = profile['sexuality']
            politics = profile['politics']
            language = profile['language']

        return render_template("profile.html", age=age, country=country, countries=countries, gender=gender, gender_options=gender_options, sexuality=sexuality, sexualities=sexualities, politics=politics, politics_options=politics_options, language=language, languages=languages)

@app.route("/privacy_policy")
def privacy_policy():
    return render_template("privacy_policy.html")

@app.route("/terms")
def terms_of_service():
    return render_template("terms.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
