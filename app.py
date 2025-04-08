from flask import Flask, render_template, session, request, redirect, flash
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
import sqlite3 as sql
import time

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = "users.db"



def login_required(f):
    """" 
    Decorates routes that need a log in.     
    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("userid") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """ Log In """
    #clear any current user info
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            flash("Must include username")
            return render_template("login.html")
        return redirect("/index")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """ Register new users """

    # if they have submitted the form start registration
    try:
        if request.method == "POST":
            username = request.form.get("username")
            if not username:
                flash("Must include username")
                return render_template("register.html")
            # set up database
            conn = sql.connect(db)
            cursor = conn.cursor()
            # Query for username
            try:
                cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                if username == cursor.fetchone()[0]:
                    flash("username already exists")
                    time.sleep(0.5)
                    return render_template("register.html")
            except:
                pass1 = request.form.get("password")
                conf = request.form.get("confirmation")
                if not pass1 or not conf:
                    flash("Must inlcude password and confrimation")
                    time.sleep(0.5)
                    return render_template("register.html")
                if pass1 != conf:
                    flash("Must password and confirmation must match")
                    time.sleep(0.5)
                    return render_template("register.html")
                # hash the password for secure storage
                pass_hash = generate_password_hash(pass1, method='scrypt', salt_length=16)
                # insert username and password into 
                cursor.execute("INSERT INTO users (username, pass_hash) VALUES (?, ?)", (username, pass_hash))
                cursor.commit()
                cursor.close()
                return redirect("/")
    except sql.Error as e:
        flash("Error registering please try again")
        print(e)
        time.sleep(0.5)
        return redirect("/register")
    
    return render_template("register.html")

