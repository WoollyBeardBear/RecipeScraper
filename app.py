from flask import Flask, render_template, session, request, redirect, flash
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from recipescraper.recipescraper.spiders.RecipeSpider import RecipeSpider
import datetime
import sqlite3 as sql
import time
import re

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
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def run_spider(url):
    settings = Settings()
    print("NOW RUNNING SPIDER")
    crawler_process = CrawlerProcess(settings)
    results = []

    def item_scraped(item, response, spider):
        print("GOT ITEM")
        results.append(item)   
    crawler = crawler_process.create_crawler(RecipeSpider)
    crawler.signals.connect(item_scraped, signal=scrapy.signals.item_scraped)
    crawler.crawl(crawler, recipe_url=url)
    crawler_process.start()
    crawler_process.stop()
    return results

def store_recipe(recipe_data):
    conn.sqlite3.connect("users.db")
    cursor = conn.cursor()
    title_slug = slugify(recipe_data.get('title', 'untitled'))
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            user_id INTEGER FOREIGN KEY,
            slug TEXT UNIQUE,
            url TEXT PRIMARY KEY,
            title TEXT,
            ingredients TEXT, --Store as JSON String
            instructions TEXT --Store as JSON String
    )
    ''')
    cursor.execute('''
    INSERT OR REPLACE INTO recipes (user_id, url, title, ingredients, instructions) 
    VALUES (?, ?, ?, ?, ?)
    ''', (session.get("user_id"), title_slug, recipe_data['source_url'], recipe_data.get('title'), json.dumps(recipe_data['ingredients']), json.dumps(recipe_data['instructions'])))
    conn.commit()
    conn.close()


@app.route("/")
@login_required
def index():
    
    
    return render_template("index.html")

def fetch_recipe_from_storage(recipe_slug):
    conn = sqlite3.connect('recipes.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT title, ingredients, instructions, url FROM recipes WHERE slug = ?''', (recipe_slug,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            'title': result[0],
            'ingredients': json.loads(result[1]),
            'instructions': json.loads(result[2]),
            'url': result[3]
        }
    return None


def slugify(title):
    """Converts a title into a URL-safe slug."""
    title = title.lower().strip()
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[-\s]+', '-', title)
    return title

@app.route("/recipe_display/<slug>")
@login_required
def recipe_display(slug):
    recipe = fetch_recipe_from_storage(slug)
    if recipe:
        return render_template("recipe_display.html", recipe=recipe)
    else:
        return "Recipe not found"

@app.route("/add_recipe", methods=["GET", "POST"])
@login_required
def add_recipe():
    if request.method == "POST":
        recipe_url = request.form.get("recipe_url")
        print(f"Scraping data from {recipe_url}")
        scraped_data = run_spider(recipe_url)
        if scraped_data:
            print("Data scraped, storing data")
            store_recipe(scraped_data)
            return render_template('recipe_display.html', recipe=scraped_data)
        else:
            return "Scraping failed or no data found."
    return render_template("add_recipe.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Log In """
    #clear any current user info
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            flash("Must include username")
            return render_template("login.html")
        if not password:
            flash("Must include password")
            return render_template("login.html")
        
        # use with to handle connection to DB
        with sql.connect(db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            
            try: 
                user_info = cursor.fetchone()
                print(check_password_hash(user_info[2], password))
                if check_password_hash(user_info[2], password):
                    session["user_id"] = user_info[0]
                    session["username"] = request.form.get("username")
                    return redirect("/")
                else:
                    flash("username/password incorrect")
                    return render_template("login.html")
            except sql.Error as e:
                print(e)
                flash("username/password incorrect")
                return render_template("login.html")
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
                conn.commit()
                conn.close()
                return redirect("/")
    except sql.Error as e:
        flash("Error registering please try again")
        print(e)
        time.sleep(0.5)
        return redirect("/register")
    
    return render_template("register.html")

