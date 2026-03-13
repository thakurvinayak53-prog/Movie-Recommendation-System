import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User
from recommender import (
    get_recommendations,
    search_movies,
    fetch_movie_details
)

app = Flask(__name__)

# ==============================
# CONFIGURATION
# ==============================

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ==============================
# LOGIN MANAGER SETUP
# ==============================

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# ==============================
# HOME + TRENDING
# ==============================

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    recommendations = None
    trending = []

    if request.method == "POST":
        movie_name = request.form.get("movie_name")
        recommendations = get_recommendations(movie_name)
    else:
        trending_titles = [
            "Oppenheimer",
            "Dune: Part Two",
            "The Dark Knight",
            "Inception",
            "Interstellar"
        ]

        for title in trending_titles:
            trending.append(fetch_movie_details(title))

    return render_template(
        "index.html",
        recommendations=recommendations,
        trending=trending
    )

# ==============================
# SEARCH API
# ==============================

@app.route("/search")
@login_required
def search():
    query = request.args.get("q")
    results = search_movies(query)
    return jsonify(results)

# ==============================
# LOGIN
# ==============================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password")

    return render_template("login.html")

# ==============================
# REGISTER
# ==============================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")

        password = generate_password_hash(
            request.form.get("password"),
            method="pbkdf2:sha256"
        )

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")

# ==============================
# CHANGE PASSWORD
# ==============================

@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")

        if not check_password_hash(current_user.password, current_password):
            flash("Current password is incorrect")
            return redirect(url_for("change_password"))

        current_user.password = generate_password_hash(
            new_password,
            method="pbkdf2:sha256"
        )
        db.session.commit()

        flash("Password updated successfully")
        return redirect(url_for("index"))

    return render_template("change_password.html")

# ==============================
# LOGOUT
# ==============================

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ==============================
# RUN APP
# ==============================

if __name__ == "__main__":
    app.run(debug=True, port=8000)