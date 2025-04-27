from flask import Flask, render_template, session, request, redirect, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import *
from psycopg2.extras import DictCursor
from new_scraper import *
import datetime
import time
import re
import psycopg2
import os
import threading


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DATABASE_URL = os.environ.get("DATABASE_URL")
@app.context_processor
def inject_now():
    """ Inject current time into templates """
    return {"now" : datetime.datetime.now()}


@app.route("/")
@login_required
def index():
    """ Home page """
    return render_template("index.html")

@app.route("/logout")
@login_required
def logout():
    """ Log out user """
    session.clear()
    return redirect("/login")

@app.route("/browse")
@login_required
def browse():
    """ Browse recipes """
    search_query = ""
    recipes = []
    conn = None
    cursor = None
    try:
        if "user_id" not in session:
            return redirect("/login")
        
        
        conn = get_db() # Connect to the database
        cursor = conn.cursor(cursor_factory=DictCursor)
        search_query = request.args.get("search", "").strip()
        user_id = int(session["user_id"])
        if search_query:
            search_pattern = f"%{search_query}%"
            cursor.execute("SELECT * FROM recipes WHERE user_id = %s AND LOWER(title) LIKE LOWER(%s) ORDER BY title", (user_id, search_pattern))

        else:
            cursor.execute("SELECT * FROM recipes WHERE user_id = %s ORDER BY title", (user_id,))

        recipes = cursor.fetchall()    
            
    except psycopg2.Error as e:
        print(f"Database error in browse route: {e}")
        flash("An error occurred while retrieving recipes. Please try again later.", "danger")
        recipes = [] 
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}") # Catch other potential errors
        flash("An unexpected error occurred.", "danger")
        recipes = []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


    return render_template("browse.html", recipes=recipes, search_query=search_query)

# ADD manual recipe entry 

@app.route("/recipe_display/<slug>")
@login_required
def recipe_display(slug):
    """ Display a recipe """
    recipe = fetch_recipe_from_storage(slug)
    if recipe:
        return render_template("recipe_display.html", recipe=recipe)
    else:
        return "Recipe not found"

@app.route("/add_recipe", methods=["GET", "POST"])
@login_required
def add_recipe():
    """ Add a recipe """
    if request.method == "POST":
        recipe_url = request.form.get("recipe_url")
        print(f"Scraping data from {recipe_url}")
        if not recipe_url:
            flash("Must include a recipe URL")
            return render_template("add_recipe.html")
        try:
            scraped_data = new_scraper(recipe_url)
            if scraped_data:
                store_recipe(scraped_data)
            return render_template("scraping_in_progress.html", success=True, error_message=None)
        except Exception as e:
            return render_template("scraping_in_progress.html", success=False, error_message=str(e))
    return render_template("add_recipe.html")

@app.route("/scraping_in_progress/<path:url>")
@login_required
def scraping_in_progress(url):
    """Displays a page indicating that scraping is in progress."""
    return render_template("scraping_in_progress.html", url=url)


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Log In """
    #clear any current user info
    session.clear()
    conn = None
    cursor = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            flash("Must include username")
            return render_template("login.html")
        if not password:
            flash("Must include password")
            return render_template("login.html")
        
        conn = get_db()
        cursor = conn.cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        
        try: 
            user_info = cursor.fetchone()
            if user_info:
                print(check_password_hash(user_info[2], password))
                if check_password_hash(user_info[2], password):
                    session["user_id"] = user_info[0]
                    session["username"] = username
                    return redirect("/")
                else:
                    flash("username/password incorrect")
                    return render_template("login.html")
            else:
                flash("username/password incorrect")
                return render_template("login.html")
        except psycopg2.Error as e:
            print(e)
            flash("An error occurred please try again", "danger")
            if conn:
                conn.rollback()

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
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
            conn = get_db()
            cursor = conn.cursor(cursor_factory=DictCursor)
            # Query for username
            try:
                cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
                if username == cursor.fetchone()[0]:
                    flash("username already exists")
                    return render_template("register.html")
            except:
                pass1 = request.form.get("password")
                conf = request.form.get("confirmation")
                if not pass1 or not conf:
                    flash("Must inlcude password and confrimation")
                    return render_template("register.html")
                if pass1 != conf:
                    flash("Must password and confirmation must match")
                    return render_template("register.html")
                # hash the password for secure storage
                pass_hash = generate_password_hash(pass1, method='scrypt', salt_length=16)
                # insert username and password into 
                cursor.execute("INSERT INTO users (username, pass_hash) VALUES (%s, %s)", (username, pass_hash))
                conn.commit()
                conn.close()
                return redirect("/")
    except psycopg2.Error as e:
        flash("Error registering please try again")
        print(e)
        return redirect("/register")
    
    return render_template("register.html")
