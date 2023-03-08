import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")
# if not info.API_KEY:
#     raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # query the users db
    row_users = db.execute("SELECT username, cash FROM users where id = ?", session["user_id"])
    cash = row_users[0]["cash"]
    username = row_users[0]["username"]

    # query the transactions db
    # (not required here) To get the data irrespective of the user   -->    # SELECT username,stock,SUM(shares)
                                                                            # FROM transactions
                                                                            # GROUP BY username,stock
                                                                            # ;

    # to get transactions of a single user with sum of same stock shares -->    # SELECT stock,SUM(shares) as s
                                                                                # FROM transactions
                                                                                # WHERE username = 'aman'
                                                                                # GROUP BY stock
                                                                                # ;

    rows_transactions = db.execute("SELECT stock,SUM(shares) as s FROM transactions WHERE username = ? GROUP BY stock", username)
    

    finalTotal = cash
    list_dicts = []
    for row in rows_transactions:
        lookup_dict = lookup(row["stock"])
        list_dicts.append({
            "symbol" : lookup_dict["symbol"],
            "name" : lookup_dict["name"],
            "shares": row["s"],
            "price" : lookup_dict["price"],
            "total": row["s"] * lookup_dict["price"]
        })
        finalTotal += row["s"] * lookup_dict["price"]


    # symbol, name, shares, price, total
    # cash
    # TOTAL
    return render_template("index.html", list_dicts=list_dicts, cash=cash, finalTotal=finalTotal)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)
        # get number of shares
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Enter valid number of shares", 403)
        if shares <= 0:
            return apology("Enter valid number of shares", 403)

        data_dict = lookup(request.form.get("symbol"))
        if not data_dict:
            return apology("Stock not found!", 403)
        
        total_cost = shares*data_dict["price"]
        # query the db for cash
        row = db.execute("SELECT username, cash FROM users where id = ?", session["user_id"])
        cash = row[0]["cash"]

        if cash < total_cost:
            return apology("Insufficient Funds", 403)
        
        # update user's cash
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash-total_cost, session["user_id"])

        # record transaction
        db.execute("INSERT INTO transactions (username,stock,stock_price,shares) VALUES(?,?,?,?)", row[0]["username"], data_dict["symbol"], data_dict["price"], shares)

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # query the users db
    row_users = db.execute("SELECT username FROM users where id = ?", session["user_id"])
    username = row_users[0]["username"]
    # query the transactions of the user
    rows_transactions = db.execute("SELECT * FROM transactions WHERE username = ?", username)

    return render_template("history.html", list_dicts=rows_transactions)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)
        data_dict = lookup(request.form.get("symbol"))
        if not data_dict:
            return apology("Stock not found!", 403)
        return render_template("quoted.html", data_dict=data_dict, usd=usd)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password", 403)
        
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 403)
        
        # Query database for username
        row = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        
        # username duplicacy check
        if len(row) == 1:
            return apology("username already exists", 403)
        
        db.execute("INSERT INTO users (username, hash) VALUES(?,?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
        
        # Redirect user to login form
        return redirect("/")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must provide symbol", 403)
        # get number of shares
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Enter valid number of shares", 403)
        if shares <= 0:
            return apology("Enter valid number of shares", 403)
        
        # query the users db
        row_users = db.execute("SELECT username,cash FROM users where id = ?", session["user_id"])
        username = row_users[0]["username"]
        cash = row_users[0]["cash"]
        # query the db for shares
        row_transactions = db.execute("SELECT stock,SUM(shares) as s FROM transactions WHERE username = ? AND stock = ? GROUP BY stock", username, request.form.get("symbol"))
         # Ensure user owns that symbol's shares
        if len(row_transactions) == 0:
            return apology("Stock not owned", 403)

        if shares > int(row_transactions[0]["s"]):
            return apology("Insufficient stocks owned",403)

        # lookup current stock price
        data_dict = lookup(request.form.get("symbol"))
        if not data_dict:
            return apology("Stock not found!", 403)
        
        selling_price = shares*data_dict["price"]
        # update user's cash
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + selling_price, session["user_id"])

        # record transaction
        db.execute("INSERT INTO transactions (username,stock,stock_price,shares) VALUES(?,?,?,?)", username, data_dict["symbol"], data_dict["price"], -shares)

        return redirect("/")
    else:
        # query the users db
        row_users = db.execute("SELECT username FROM users where id = ?", session["user_id"])
        username = row_users[0]["username"]
        # query the transactions db to get stock owned
        stocks = db.execute("SELECT stock FROM transactions WHERE username = ? GROUP BY stock", username)
        
        return render_template("sell.html", stocks=stocks)