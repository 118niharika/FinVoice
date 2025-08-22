from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__, template_folder="templates")
DB_PATH = "finvoice.sqlite"

# ==============================
# DB Setup
# ==============================
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts DATETIME,
            description TEXT,
            amount REAL NOT NULL,
            category TEXT
        )
    """)
    return conn

# ==============================
# Categorizer
# ==============================
rules = {
    "Food": ["food","dinner","lunch","breakfast","meal","snacks","restaurant","pizza","burger","cafe","chai","zomato","swiggy","dining"],
    "Travel": ["uber","ola","auto","bus","train","flight","taxi","fuel","petrol","diesel","ticket","metro","travelling"],
    "Bills": ["bill","electricity","wifi","internet","rent","recharge","mobile","gas","water"],
    "Shopping": ["amazon","flipkart","shopping","clothes","shoes","tshirt","jeans","electronics","gadget"],
    "Health": ["medicine","pharmacy","doctor","hospital","health","gym","fitness"],
    "Entertainment": ["movie","netflix","prime","spotify","game","concert","theatre"],
    "Education": ["book","course","tuition","exam","fee","college","coaching"]
}

def categorize(text: str) -> str:
    t = text.lower()
    for cat, words in rules.items():
        if any(w in t for w in words):
            return cat
    return "Other"

# ==============================
# Date parser (today / yesterday)
# ==============================
def parse_datetime_from_text(text: str):
    t = text.lower()
    if "yesterday" in t or "kal" in t:   # Hindi "kal"
        dt = datetime.now() - timedelta(days=1)
    elif "today" in t or "aaj" in t:     # Hindi "aaj"
        dt = datetime.now()
    else:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# ==============================
# Advisor
# ==============================
def build_insights(last30, monthly_target_sip: int = 2000):
    total = sum(e["amount"] for e in last30)
    by_cat = {}
    for e in last30:
        by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]

    top_cat, top_amt = ("N/A", 0)
    if by_cat:
        top_cat, top_amt = max(by_cat.items(), key=lambda x: x[1])

    suggestions = []
    if total > 0:
        suggestions.append(f"Your spend in the last 30 days is ₹{total:.0f}.")
        if top_cat != "N/A":
            cut = max(50, round(0.10 * top_amt))
            #suggestions.append(f"Reduce {top_cat} spending by ~₹{cut} (10%) this month.")
            #suggestions.append("Redirect that to SIP to reach your goal faster.")
    else:
        suggestions.append("Start logging expenses to get personalized tips.")

    monthly = max(500, round(0.10 * total))
    sip = max(monthly, monthly_target_sip)

    def sip_future_value(p, r=0.12, months=36):
        i = r/12
        return p * (( (1+i)**months - 1 ) / i) * (1+i)

    fv3y = round(sip_future_value(sip, 0.12, 36))

    return {
        "total": total,
        "byCat": by_cat,
        "topCategory": top_cat,
        "suggestions": suggestions,
        "sipProposal": {
            "monthly": sip,
            "horizonMonths": 36,
            "projectedValue": fv3y
        }
    }

# ==============================
# Routes
# ==============================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/add_expense", methods=["POST"])
def add_expense():
    data = request.json
    desc = data.get("description","Expense")
    amount = float(data.get("amount",0))
    if amount <= 0:
        return jsonify({"error":"Invalid amount"}), 400

    # date parsing if voice text contains today/yesterday
    ts = parse_datetime_from_text(desc)

    cat = categorize(desc)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO expenses(ts, description, amount, category) VALUES (?,?,?,?)",
                (ts, desc, amount, cat))
    conn.commit()
    return jsonify({"message":"Expense added","category":cat})

@app.route("/expenses", methods=["GET"])
def get_expenses():
    conn = get_db()
    rows = conn.execute("SELECT * FROM expenses WHERE ts >= datetime('now','-30 days') ORDER BY ts DESC").fetchall()
    data = [dict(r) for r in rows]

    # also return advisor insights
    insights = build_insights(data)

    return jsonify({
        "expenses": data,
        "insights": insights
    })

if __name__ == "__main__":
    app.run(debug=True)