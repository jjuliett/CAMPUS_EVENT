from flask import Flask, request
from flask_cors import CORS

students = [{"id": 1, "name": "Alice Martin", "email": "alice@example.com", "filiere": "Informatique"},
            {"id": 2, "name": "Bob Durand", "email": "bob@example.com", "filiere": "Mathématiques"},
            {"id": 3, "name": "Sarah Benali", "email": "sarah@example.com", "filiere": "Gestion"}]
events = [{"id": 1, "title": "Atelier Python", "date": "2026-11-20", "location": "Salle B12", "capacity": 30},
          {"id": 2, "title": "Forum Entreprises", "date": "2026-11-25", "location": "Amphi A", "capacity": 50},
          {"id": 3, "title": "Conférence IA & Éthique", "date": "2026-12-02", "location": "Amphi C", "capacity": 1}]
registrations = [{"id": 1, "student_id": 1, "event_id": 1, "status": "accepted"},
                 {"id": 2, "student_id": 2, "event_id": 2, "status": "pending"},
                 {"id": 3, "student_id": 1, "event_id": 3, "status": "pending"}]

app = Flask(__name__)
CORS(app)


def find(items, id):
    return next((item for item in items if str(item["id"]) == str(id)), None)


def count_registrations(event_id):
    return len([r for r in registrations if r["event_id"] == event_id and r["status"] != "rejected"])


def with_places(event):
    places = event["capacity"] - count_registrations(event["id"])
    return {**event, "available_places": max(places, 0)}


@app.route("/")
def hello_world():
    return "<p>Campus Event API</p>"

@app.route("/events", methods=["GET"])
def get_events():
    return {"events": [with_places(e) for e in events]}, 200

@app.route("/events/<id>", methods=["GET"])
def get_event(id):
    event = find(events, id)
    if event:
        return {"event": with_places(event)}, 200
    else:
        return {"error": "Event not found"}, 404

@app.route("/students", methods=["GET"])
def get_students():
    return {"students": students}, 200

@app.route("/registrations", methods=["POST"])
def create_registration():
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    event_id = data.get("event_id")

    if student_id is None or event_id is None:
        return {"error": "student_id and event_id are required"}, 400
    if not find(students, student_id):
        return {"error": "Student not found"}, 404
    event = find(events, event_id)
    if not event:
        return {"error": "Event not found"}, 404

    student_id = int(student_id)
    event_id = int(event_id)

    for r in registrations:
        if r["student_id"] == student_id and r["event_id"] == event_id:
            return {"error": "Student already registered to this event"}, 409
    if count_registrations(event_id) >= event["capacity"]:
        return {"error": "Event is full"}, 409

    new_registration = {
        "id": max([r["id"] for r in registrations], default=0) + 1,
        "student_id": student_id,
        "event_id": event_id,
        "status": "pending"
    }
    registrations.append(new_registration)
    return {"message": "Registration created successfully", "registration": new_registration}, 201

@app.route("/registrations", methods=["GET"])
def get_registrations():
    return {"registrations": registrations}, 200

@app.route("/registrations/<id>", methods=["GET"])
def get_registration(id):
    registration = find(registrations, id)
    if registration:
        return {"registration": registration}, 200
    else:
        return {"error": "Registration not found"}, 404

@app.route("/registrations/<id>", methods=["PATCH"])
def update_registration(id):
    registration = find(registrations, id)
    if not registration:
        return {"error": "Registration not found"}, 404

    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ["pending", "accepted", "rejected"]:
        return {"error": "status must be pending, accepted or rejected"}, 400

    registration["status"] = status
    return {"message": "Status updated", "registration": registration}, 200

if __name__ == "__main__":
    app.run(debug=True)
