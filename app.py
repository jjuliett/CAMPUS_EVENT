import os
import sqlite3
from flask import Flask, request
from flask_cors import CORS

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "campus_event.db")

students = [{"id": 1, "name": "Alice Martin", "email": "alice@example.com", "filiere": "Informatique"},
            {"id": 2, "name": "Bob Durand", "email": "bob@example.com", "filiere": "Mathématiques"},
            {"id": 3, "name": "Sarah Benali", "email": "sarah@example.com", "filiere": "Gestion"}]
events = [{"id": 1, "title": "Atelier Python", "date": "2026-11-20", "location": "Salle B12", "capacity": 30},
          {"id": 2, "title": "Forum Entreprises", "date": "2026-11-25", "location": "Amphi A", "capacity": 50},
          {"id": 3, "title": "Conférence IA & Éthique", "date": "2026-12-02", "location": "Amphi C", "capacity": 1}]
registrations = [{"id": 1, "student_id": 1, "event_id": 1, "status": "accepted"},
                 {"id": 2, "student_id": 2, "event_id": 2, "status": "pending"},
                 {"id": 3, "student_id": 1, "event_id": 3, "status": "pending"}]

STATUSES = ["pending", "accepted", "rejected", "waitlisted"]

app = Flask(__name__)
CORS(app)


def get_db():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    db.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, filiere TEXT)""")
    db.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY, title TEXT NOT NULL, date TEXT, location TEXT, capacity INTEGER NOT NULL)""")
    db.execute("""CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL REFERENCES students(id),
        event_id INTEGER NOT NULL REFERENCES events(id),
        status TEXT NOT NULL)""")

    if db.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        for s in students:
            db.execute("INSERT INTO students VALUES (?, ?, ?, ?)", (s["id"], s["name"], s["email"], s["filiere"]))
        for e in events:
            db.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?)", (e["id"], e["title"], e["date"], e["location"], e["capacity"]))
        for r in registrations:
            db.execute("INSERT INTO registrations VALUES (?, ?, ?, ?)", (r["id"], r["student_id"], r["event_id"], r["status"]))
    db.commit()
    db.close()


def find(db, table, id):
    row = db.execute(f"SELECT * FROM {table} WHERE id = ?", (id,)).fetchone()
    return dict(row) if row else None


def count_registrations(db, event_id):
    return db.execute("SELECT COUNT(*) FROM registrations WHERE event_id = ? AND status IN ('pending', 'accepted')",
                      (event_id,)).fetchone()[0]


def with_places(db, event):
    places = event["capacity"] - count_registrations(db, event["id"])
    waiting = db.execute("SELECT COUNT(*) FROM registrations WHERE event_id = ? AND status = 'waitlisted'",
                         (event["id"],)).fetchone()[0]
    return {**event, "available_places": max(places, 0), "waitlist": waiting}


def promote_waitlist(db, event_id):
    event = find(db, "events", event_id)
    if count_registrations(db, event_id) < event["capacity"]:
        first = db.execute("SELECT id FROM registrations WHERE event_id = ? AND status = 'waitlisted' ORDER BY id LIMIT 1",
                           (event_id,)).fetchone()
        if first:
            db.execute("UPDATE registrations SET status = 'pending' WHERE id = ?", (first["id"],))


@app.route("/")
def hello_world():
    return "<p>Campus Event API</p>"

@app.route("/events", methods=["GET"])
def get_events():
    db = get_db()
    rows = db.execute("SELECT * FROM events ORDER BY date").fetchall()
    result = [with_places(db, dict(r)) for r in rows]
    db.close()
    return {"events": result}, 200

@app.route("/events/<id>", methods=["GET"])
def get_event(id):
    db = get_db()
    event = find(db, "events", id)
    if event:
        event = with_places(db, event)
    db.close()
    if event:
        return {"event": event}, 200
    else:
        return {"error": "Event not found"}, 404

@app.route("/students", methods=["GET"])
def get_students():
    db = get_db()
    rows = db.execute("SELECT * FROM students ORDER BY name").fetchall()
    db.close()
    return {"students": [dict(r) for r in rows]}, 200

@app.route("/registrations", methods=["POST"])
def create_registration():
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    event_id = data.get("event_id")

    if student_id is None or event_id is None:
        return {"error": "student_id and event_id are required"}, 400

    db = get_db()
    if not find(db, "students", student_id):
        db.close()
        return {"error": "Student not found"}, 404
    event = find(db, "events", event_id)
    if not event:
        db.close()
        return {"error": "Event not found"}, 404

    already = db.execute("SELECT id FROM registrations WHERE student_id = ? AND event_id = ?",
                         (student_id, event_id)).fetchone()
    if already:
        db.close()
        return {"error": "Student already registered to this event"}, 409

    if count_registrations(db, event["id"]) >= event["capacity"]:
        status = "waitlisted"
        message = "Event is full, registration added to the waitlist"
    else:
        status = "pending"
        message = "Registration created successfully"

    cursor = db.execute("INSERT INTO registrations (student_id, event_id, status) VALUES (?, ?, ?)",
                        (int(student_id), event["id"], status))
    db.commit()
    new_registration = find(db, "registrations", cursor.lastrowid)
    db.close()
    return {"message": message, "registration": new_registration}, 201

@app.route("/registrations", methods=["GET"])
def get_registrations():
    db = get_db()
    rows = db.execute("SELECT * FROM registrations ORDER BY id").fetchall()
    db.close()
    return {"registrations": [dict(r) for r in rows]}, 200

@app.route("/registrations/<id>", methods=["GET"])
def get_registration(id):
    db = get_db()
    registration = find(db, "registrations", id)
    db.close()
    if registration:
        return {"registration": registration}, 200
    else:
        return {"error": "Registration not found"}, 404

@app.route("/registrations/<id>", methods=["PATCH"])
def update_registration(id):
    db = get_db()
    registration = find(db, "registrations", id)
    if not registration:
        db.close()
        return {"error": "Registration not found"}, 404

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in STATUSES:
        db.close()
        return {"error": "status must be pending, accepted, rejected or waitlisted"}, 400

    takes_place = status in ["pending", "accepted"]
    had_place = registration["status"] in ["pending", "accepted"]
    event = find(db, "events", registration["event_id"])
    if takes_place and not had_place and count_registrations(db, event["id"]) >= event["capacity"]:
        db.close()
        return {"error": "Event is full"}, 409

    db.execute("UPDATE registrations SET status = ? WHERE id = ?", (status, id))
    if had_place and status == "rejected":
        promote_waitlist(db, event["id"])
    db.commit()
    registration = find(db, "registrations", id)
    db.close()
    return {"message": "Status updated", "registration": registration}, 200

init_db()

if __name__ == "__main__":
    app.run(debug=True)
