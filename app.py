from flask import Flask, render_template, session, request, redirect
from functools import wraps

app = Flask(__name__)

app.secret_key = '0621997fa18b0180425312909aae0a0881b47747e3632c3f38b3989be04966d9'

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
    return decorated_fuction


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["username"] = request.form["username"]
        return redirect("/index")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        session["username"] = request.form["username"]
        return redirect("/index")
    
    return render_template("register.html")

