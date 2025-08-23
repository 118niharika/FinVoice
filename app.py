from flask import Flask, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route("/")
def home():
    # Always start with index.html (your login page)
    return redirect(url_for("login"))

@app.route("/login")
def login():
    return render_template("index.html")   # index.html is your login

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "user" in session:   # check if user is logged in
        return render_template("dashboard.html")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
