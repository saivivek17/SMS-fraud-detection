from flask import Flask, render_template, request, redirect, url_for, session, flash
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from joblib import load
import nltk
import warnings
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

warnings.filterwarnings("ignore", category=RuntimeWarning)

try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change later for production security

# Database setup
DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

MODEL_PATH = os.path.join("models", "spam_best_model.pkl")
model = load(MODEL_PATH)

def preprocess_data(text):
    stop_words = set(stopwords.words('english'))
    porter = PorterStemmer()
    words = [
        porter.stem(word.lower())
        for word in text.split()
        if word.lower() not in stop_words
    ]
    return " ".join(words)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if not session.get('user'):
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        sms = request.form.get('sms')
        if not sms:
            flash("Please enter SMS!", "danger")
            return redirect(url_for('predict'))

        result = "spam"
        return render_template("result.html", sms=sms, result=result)

    return render_template("predict.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users(username, email, password) VALUES (?, ?, ?)",
                        (username, email, hashed_password))
            conn.commit()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for("login_page"))
        except:
            flash("Email already registered!", "danger")
        finally:
            conn.close()

    return render_template("signup.html")


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user"] = {"id": user[0], "username": user[1], "email": user[2]}
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid Email or Password", "danger")

    return render_template("login.html")


@app.route('/dashboard')
def dashboard():
    if "user" not in session:
        flash("Please login first", "warning")
        return redirect(url_for("login_page"))
    return render_template("dashboard.html", user=session["user"])

@app.route('/logout')
def logout():
    session.pop("user", None)
    flash("Logged out successfully", "info")
    return redirect(url_for("home"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        # TODO: Add your email lookup and reset process here
        flash("Password reset instructions will be sent if email exists", "info")
        return redirect(url_for("login_page"))

    return render_template("forgot_password.html")


@app.route('/about')
def about_page():
    return render_template('about.html')


if __name__ == "__main__":
    app.run(debug=True)
