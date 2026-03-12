import os
import sqlite3
from flask_bcrypt import Bcrypt
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd

app = Flask(__name__)
app.secret_key = "replace_this_with_random_secret" 
bcrypt=Bcrypt(app)

DIR = os.path.dirname(os.path.abspath(__file__))
AIR_CSV = os.path.join(DIR, "airline.csv")
TRAIN_CSV = os.path.join(DIR, "train.csv")
BUS_CSV = os.path.join(DIR, "bus.csv")
HOTEL_CSV = os.path.join(DIR, "hotel.csv")

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor() 

    # Users table (added name column)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Trips table
    c.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mode TEXT,
            from_city TEXT,
            to_city TEXT,
            travel_date TEXT,
            transport_name TEXT,
            hotel_name TEXT,
            total_cost INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

@app.route("/offline")
def offline():
    return render_template("offline.html")

# ------------------- HELPERS -------------------
def load_df(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    return df

def places_list():
    dfs = []
    for p in (AIR_CSV, TRAIN_CSV, BUS_CSV, HOTEL_CSV):
        if os.path.exists(p):
            dfs.append(load_df(p))
    places = set()
    for df in dfs:
        for col in ["from", "to", "location", "destination", "city", "origin"]:
            if col in df.columns:
                for v in df[col].tolist():
                    if v and str(v).strip():
                        places.add(str(v).strip())
    return sorted(places)

def df_for_mode(mode):
    if mode == "airways":
        return load_df(AIR_CSV)
    if mode == "railways":
        return load_df(TRAIN_CSV)
    if mode == "roadways":
        return load_df(BUS_CSV)
    return pd.DataFrame()

def parse_price(v):
    try:
        return int(float(str(v).strip()))
    except:
        return None

# ------------------- ROUTES -------------------
@app.route("/", methods=["GET"])
def mode():
    modes = [("airways","Airways ✈"), ("railways","Railways 🚆"), ("roadways","Roadways 🚌")]
    return render_template("mode.html", modes=modes)


@app.route("/route", methods=["GET","POST"])
def route():
    mode = request.args.get("mode")
    if not mode:
        return redirect(url_for("mode"))

    places = places_list()

    today_date = date.today()
    max_date = today_date + timedelta(days=60)

    today = today_date.isoformat()
    max_allowed = max_date.isoformat()

    return render_template(
        "route.html",
        mode=mode,
        places=places,
        today=today,
        max_allowed=max_allowed
    )


@app.route("/search", methods=["POST"])
def search():
    mode = request.form.get("mode")
    from_city = request.form.get("from_city","").strip()
    to_city = request.form.get("to_city","").strip()
    budget_raw = request.form.get("budget","").strip()
    travel_date = request.form.get("travel_date")

    if not travel_date:
        travel_date = date.today().isoformat()

    if not mode or not from_city or not to_city:
        return redirect(url_for("route", mode=mode))

    budget = None
    if budget_raw:
        if not budget_raw.isdigit():
            return render_template(
                "route.html",
                mode=mode,
                places=places_list(),
                error="Please enter a valid numeric budget."
            )
        budget = int(budget_raw)

    df = df_for_mode(mode)

    from_cols = [c for c in df.columns if "from" in c or "origin" in c]
    to_cols = [c for c in df.columns if "to" in c or "destination" in c]

    filtered = df
    if from_cols:
        filtered = filtered[filtered[from_cols[0]].str.strip().str.lower() == from_city.lower()]
    if to_cols:
        filtered = filtered[filtered[to_cols[0]].str.strip().str.lower() == to_city.lower()]

    options = []

    for _, row in filtered.iterrows():
        price = None
        for c in ["price","cost","fare"]:
            if c in row.index and row[c] != "":
                price = parse_price(row[c])
                break

        item = {
            "name": row.get("name") or row.get("vehicle") or row.get("train") or row.get("flight") or "",
            "price": price,
            "departure_time": row.get("departure_time") or "",
            "arrival_time": row.get("arrival_time") or "",
            "from": row.get(from_cols[0]) if from_cols else "",
            "to": row.get(to_cols[0]) if to_cols else "",
            "link": row.get("link") or ""
        }

        if budget is None or (price is not None and price <= budget):
            options.append(item)

    # Sort ascending
    options = sorted(options, key=lambda x: (x["price"] is None, x["price"] or 0))

    # 🔥 STORE EXACT SAME LIST USER SEES

    session["last_search"] = {
        "mode": mode,
        "from": from_city,
        "to": to_city,
        "budget": budget,
        "travel_date": travel_date
    }

    return render_template("results.html", mode=mode, options=options, budget=budget)

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("signup.html", error="Password mismatched")

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (name, username, email, password) VALUES (?,?,?,?)",
                      (name, username, email, hashed))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            return render_template("signup.html", error="Username or Email already exists")

    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        identifier = request.form["identifier"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE email=? OR username=?", (identifier, identifier))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[4], password):
            session["user_id"] = user[0]
            session["username"] = user[2]
            session["name"] = user[1]
            return redirect(url_for("mode"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/forgot_password", methods=["GET","POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("forgot_password.html", error="Password mismatched")

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("forgot_password.html")

@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM trips WHERE user_id=?", (user_id,))
    total_trips = c.fetchone()[0]

    c.execute("SELECT SUM(total_cost) FROM trips WHERE user_id=?", (user_id,))
    total_spent = c.fetchone()[0] or 0

    conn.close()

    return render_template(
        "dashboard.html",
        total_trips=total_trips,
        total_spent=total_spent
    )

@app.route("/my_trips")
def my_trips():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        SELECT id, mode, from_city, to_city, travel_date,
               transport_name, hotel_name, total_cost
        FROM trips
        WHERE user_id=?
        ORDER BY id DESC
    """, (user_id,))

    trips = c.fetchall()
    conn.close()

    return render_template("my_trips.html", trips=trips)

@app.route("/delete_trip/<int:trip_id>")
def delete_trip(trip_id):
    user_id = session.get("user_id")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("DELETE FROM trips WHERE id=? AND user_id=?", (trip_id, user_id))

    conn.commit()
    conn.close()

    return redirect(url_for("my_trips"))


@app.route("/save_trip", methods=["POST"])
def save_trip():

    user_id = session.get("user_id")
    transport = session.get("selected_transport")
    hotel = session.get("selected_hotel")
    last = session.get("last_search")

    if not user_id or not transport or not last:
        return redirect(url_for("login"))

    mode = last.get("mode")
    from_city = last.get("from")
    to_city = last.get("to")
    travel_date = last.get("travel_date")

    transport_price = transport.get("price") or 0
    hotel_price = hotel.get("price") if hotel else 0

    total = transport_price + (hotel_price or 0)

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO trips
        (user_id, mode, from_city, to_city, travel_date,
         transport_name, hotel_name, total_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        mode,
        from_city,
        to_city,
        travel_date,
        transport.get("name"),
        hotel.get("name") if hotel else None,
        total
    ))

    conn.commit()
    conn.close()

    session.pop("selected_transport", None)
    session.pop("selected_hotel", None)

    return redirect(url_for("my_trips"))

@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        email = request.form["email"]

        c.execute("""
            UPDATE users
            SET name=?, username=?, email=?
            WHERE id=?
        """, (name, username, email, user_id))

        conn.commit()
        session["name"] = name
        session["username"] = username

    c.execute("SELECT name, username, email FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()

    return render_template("profile.html", user=user)


@app.route("/select_transport", methods=["POST"])
def select_transport():

    idx = int(request.form.get("index", -1))
    last = session.get("last_search")

    if not last:
        return redirect(url_for("mode"))

    mode = last.get("mode")
    from_city = last.get("from")
    to_city = last.get("to")
    budget = last.get("budget")

    df = df_for_mode(mode)

    from_cols = [c for c in df.columns if "from" in c or "origin" in c]
    to_cols = [c for c in df.columns if "to" in c or "destination" in c]

    filtered = df
    if from_cols:
        filtered = filtered[filtered[from_cols[0]].str.strip().str.lower() == from_city.lower()]
    if to_cols:
        filtered = filtered[filtered[to_cols[0]].str.strip().str.lower() == to_city.lower()]

    options = []

    for _, row in filtered.iterrows():
        price = None
        for c in ["price","cost","fare"]:
            if c in row.index and row[c] != "":
                price = parse_price(row[c])
                break

        item = {
            "name": row.get("name") or "",
            "price": price,
            "to": row.get(to_cols[0]) if to_cols else "",
            "link": row.get("link") or ""
        }

        if budget is None or (price is not None and price <= budget):
            options.append(item)

    # 🔥 SAME SORTING AS SEARCH
    options = sorted(options, key=lambda x: (x["price"] is None, x["price"] or 0))

    if idx >= len(options):
        return redirect(url_for("mode"))

    session["selected_transport"] = options[idx]

    return redirect(url_for("ask_hotel"))

@app.route("/skip_hotel")
def skip_hotel():
    session.pop("selected_hotel_index", None)
    return redirect(url_for("summary"))


@app.route("/ask_hotel")
def ask_hotel():

    transport = session.get("selected_transport")
    last = session.get("last_search")

    if not transport or not last:
        return redirect(url_for("mode"))

    budget = last.get("budget")
    transport_price = transport.get("price") or 0
    destination = transport.get("to")

    df = load_df(HOTEL_CSV)
    hotels = []

    for _, row in df.iterrows():
        price = None
        for c in ["price","cost","rate"]:
            if c in row.index and row[c] != "":
                price = parse_price(row[c])
                break

        if destination.lower() in (row.get("location","") + row.get("city","") + row.get("destination","")).lower():
            hotels.append({
                "name": row.get("name") or "",
                "price": price,
                "location" : row.get("location") or "",
                "link": row.get("link") or ""
            })

    remaining = None
    message = None

    if budget is not None:
        remaining = budget - transport_price
        
        if remaining <= 0:
            hotels = []
            message = "No hotels available within budget"
        else:
            hotels = [h for h in hotels if h["price"] is not None and h["price"] <= remaining]

    # Sort hotels ascending
    hotels = sorted(hotels, key=lambda x: (x["price"] is None, x["price"] or 0))

    return render_template(
        "ask_hotel.html",
        hotels=hotels,
        dest=destination,
        remaining=remaining,
        message=message
    )

@app.route("/select_hotel", methods=["POST"])
def select_hotel():

    idx = int(request.form.get("index", -1))
    last = session.get("last_search")
    transport = session.get("selected_transport")

    if not last or not transport:
        return redirect(url_for("mode"))

    budget = last.get("budget")
    transport_price = transport.get("price") or 0
    destination = transport.get("to")

    df = load_df(HOTEL_CSV)

    hotels = []

    if not df.empty:
        hotel_cols = [c for c in df.columns if "location" in c or "city" in c or "destination" in c]

        if hotel_cols:
            hdf = df[df[hotel_cols[0]].str.strip().str.lower() == destination.lower()]
        else:
            hdf = df

        for _, row in hdf.iterrows():
            price = None
            for c in ["price","cost","rate"]:
                if c in row.index and row[c] != "":
                    price = parse_price(row[c])
                    break

            hotels.append({
                "name": row.get("name") or "",
                "location" : row.get("location") or "",
                "price": price,
                "link": row.get("link") or ""
            })

    # Apply SAME budget logic as ask_hotel
    if budget is not None:
        remaining = budget - transport_price

        if remaining <= 0:
            hotels = []
        else:
            hotels = [h for h in hotels if h["price"] is not None and h["price"] <= remaining]

    # 🔥 SAME SORTING
    hotels = sorted(hotels, key=lambda x: (x["price"] is None, x["price"] or 0))

    if idx < 0 or idx >= len(hotels):
        return redirect(url_for("ask_hotel"))

    session["selected_hotel"] = hotels[idx]

    return redirect(url_for("summary"))

@app.route("/summary")
def summary():

    transport = session.get("selected_transport")
    hotel = session.get("selected_hotel")
    last = session.get("last_search")

    if not transport or not last:
        return redirect(url_for("mode"))

    budget = last.get("budget")

    transport_price = transport.get("price") or 0
    hotel_price = hotel.get("price") if hotel else 0

    total = transport_price + (hotel_price or 0)

    return render_template(
        "summary.html",
        transport=transport,
        hotel=hotel,
        budget=budget,
        total=total
    )

@app.route("/back_to_results")
def back_to_results():
    last = session.get("last_search")
    if not last:
        return redirect(url_for("mode"))

    mode = last.get("mode")
    from_city = last.get("from")
    to_city = last.get("to")
    budget = last.get("budget")

    df = df_for_mode(mode)

    from_cols = [c for c in df.columns if "from" in c or "origin" in c]
    to_cols = [c for c in df.columns if "to" in c or "destination" in c]

    filtered = df
    if from_cols:
        filtered = filtered[filtered[from_cols[0]].str.strip().str.lower() == from_city.lower()]
    if to_cols:
        filtered = filtered[filtered[to_cols[0]].str.strip().str.lower() == to_city.lower()]

    options = []
    for _, row in filtered.iterrows():
        price = None
        for c in ["price","cost","fare"]:
            if c in row.index and row[c] != "":
                price = parse_price(row[c])
                break

        item = {
            "name": row.get("name") or row.get("vehicle") or row.get("train") or row.get("flight") or "",
            "price": price,
            "departure_time": row.get("departure_time") or "",
            "arrival_time": row.get("arrival_time") or "",
            "from": row[from_cols[0]] if from_cols else "",
            "to": row[to_cols[0]] if to_cols else "",
            "link": row.get("link") or ""
        }

        if budget is None or (price is not None and price <= budget):
            options.append(item)

    return render_template(
        "results.html",
        mode=mode,
        options=options,
        budget=budget
    )

@app.route("/back_to_hotels")
def back_to_hotels():
    return redirect(url_for("ask_hotel"))

# ------------------- RUN APP -------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
