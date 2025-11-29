from flask import Flask, render_template, request, jsonify, send_file
import sqlite3, joblib, csv, io
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "expenses.db"
MODEL = BASE / "model" / "expense_model.pkl"

app = Flask(__name__)

# -----------------------------
# INIT DATABASE
# -----------------------------
def init_db():
    DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        description TEXT,
        merchant TEXT,
        amount REAL,
        category TEXT
    )
    """)
    conn.commit()
    conn.close()


# -----------------------------
# ROUTES (Pages)
# -----------------------------
@app.route("/")
def home():
    init_db()
    return render_template("index.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/predictions")
def predictions():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT category, SUM(amount) FROM transactions GROUP BY category")
    rows = cur.fetchall()
    conn.close()

    preds = [
        {"category": r[0], "pred": round(r[1] * 1.10, 2)} for r in rows
    ]

    return render_template("predictions.html", preds=preds)

@app.route("/history")
def history():
    return render_template("history.html")


# -----------------------------
# API ENDPOINTS
# -----------------------------
@app.route("/api/transactions", methods=["GET", "POST", "DELETE"])
def api_transactions():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # ADD transaction
    if request.method == "POST":
        data = request.json
        date = data["date"]
        desc = data["description"]
        merch = data["merchant"]
        amount = float(data["amount"])
        category = data.get("category")

        # ML AUTOPREDICT IF CATEGORY IS EMPTY
        if not category and MODEL.exists():
            try:
                model = joblib.load(MODEL)
                feat = (desc + " " + merch).lower() + " amt_" + str(amount)
                category = model.predict([feat])[0]
            except:
                category = "Others"

        cur.execute("""
        INSERT INTO transactions(date, description, merchant, amount, category)
        VALUES(?,?,?,?,?)
        """, (date, desc, merch, amount, category))

        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "category": category})

    # DELETE
    if request.method == "DELETE":
        tid = request.args.get("id")
        cur.execute("DELETE FROM transactions WHERE id=?", (tid,))
        conn.commit()
        conn.close()
        return jsonify({"status": "deleted"})

    # GET ALL
    cur.execute("SELECT * FROM transactions ORDER BY date DESC")
    rows = cur.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "date": r[1],
            "description": r[2],
            "merchant": r[3],
            "amount": r[4],
            "category": r[5]
        })

    return jsonify(result)


@app.route("/api/categories")
def categories():
    return jsonify([
        {"name": "Food", "icon": "🍔", "color": "#ff7043"},
        {"name": "Transport", "icon": "🚌", "color": "#42a5f5"},
        {"name": "Groceries", "icon": "🛒", "color": "#66bb6a"},
        {"name": "Shopping", "icon": "🛍️", "color": "#ef5350"},
        {"name": "Bills", "icon": "💡", "color": "#ffb74d"},
        {"name": "Entertainment", "icon": "🎬", "color": "#ab47bc"},
        {"name": "Health", "icon": "💊", "color": "#26a69a"},
        {"name": "Others", "icon": "🔖", "color": "#90a4ae"}
    ])


# -----------------------------
# EXPORT CSV
# -----------------------------
@app.route("/export")
def export():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT date,description,merchant,amount,category FROM transactions")
    rows = cur.fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["date","description","merchant","amount","category"])
    cw.writerows(rows)

    output = io.BytesIO()
    output.write(si.getvalue().encode("utf-8"))
    output.seek(0)

    return send_file(output, download_name="transactions.csv", as_attachment=True)


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
