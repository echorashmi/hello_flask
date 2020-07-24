#Adding a comment to check if git status detects this change or not. 
import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session 
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

#--------------------------- Step 4
@app.route("/")
@login_required
def index():
    rows = db.execute("SELECT * FROM buys WHERE user_id = :id", id=session["user_id"])
    cash_query = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
    cash_balance = cash_query[0]['cash']
    grand_total = float(cash_balance)

    return render_template("index.html", result = rows, cash_balance = cash_balance, grand_total = grand_total)

#--------------------------- Step 3
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":
        # 3.a User Inputs a Stock Symbol - text field, name symbol.
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)
        # 3.a.i Render apology if input is blank or symbol does not exist (call lookup)
        shares = lookup(request.form.get("symbol"))
        if not shares:
            return apology("Symbol does not exist", 404)

        # 3.b Take a input number of shares - text field, name shared
        if not request.form.get("shares"):
                return apology("must provide how many shares", 403)

        # 3.b.i Render apology if not positive integer
        if int(request.form.get("shares")) < 0:
                return apology("provide positive number", 403)
        else:
            count_to_purchase = int(request.form.get("shares"))

        # 3.c Call lookup to look at the price
        print(shares) # ------- TODO

        # 3.d Find how much cash the user has
        # Query database for username
        rows = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        # Remember which user has logged in
        user_cash = rows[0]["cash"]

        # 3.f Render apology if user cannot afford number of shared at the current price
        if user_cash < (0.50*count_to_purchase): # Assume 0.50 is price per share
            return apology("Insufficient Funds", 403)
        else:
        # 3.g Store the transaction in table buys if a user has the details
            insert = "insert into buys (user_id, symbol, price_per_stock, total_shares_purchased) values(?, ?, ?, ?)"
            rows = db.execute(insert, session["user_id"], request.form.get("symbol"), 0.50, count_to_purchase)
        return render_template("buy.html")
    else:
        return render_template("buy.html")


#--------------------------- Step 6
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    rows = db.execute("SELECT * FROM transactions WHERE user_id = :id", id=session["user_id"])

    return render_template("history.html", result = rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


#--------------------------- Step 2
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)

        quote_values = lookup(request.form.get("symbol"))

        return render_template("quotes.html", result = quote_values)
    else:
        return render_template("quote.html")


#--------------------------- Step 1
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide confirmation", 403)

        # Ensure password was submitted
        elif(request.form.get("password") != request.form.get("confirmation")):
            return apology("passwords must match", 403)

        # Query database for username
        insert = "insert into users (username, hash) values(?, ?)"
        rows = db.execute(insert, request.form.get("username"), generate_password_hash(request.form.get("password")))

        '''

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)


        # Redirect user to home page
        '''
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

#--------------------------- Step 5
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        print(request.form.get("symbol"))
        print(request.form.get("shares"))

        return redirect("/")
    else:
        return render_template("sell.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
