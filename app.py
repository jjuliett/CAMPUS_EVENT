from flask import Flask, request

students = [{"id": 1, "name": "Alice", "email": "alice@example.com", "filière": "Informatique"}, 
            {"id": 2, "name": "Bob", "email": "bob@example.com", "filière": "Mathématiques"}] 
events = [{"id": 1, "title": "Math Workshop", "date": "2023-10-15", "location": "Salle 1", "capacity": 30}, 
          {"id": 2, "title": "Science Fair", "date": "2023-10-16", "location": "Salle 2", "capacity": 50}] 
registrations = [{"id": 1, "student_id": 1, "event_id": 1, "status": "confirmed"}, {"id": 2, "student_id": 2, "event_id": 2, "status": "pending"}]

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"   

@app.route("/events", methods=["GET"])
def get_events():
    return {"events": events}, 200

@app.route("/events/<id>", methods=["GET"])
def get_event(id):
    event = next((event for event in events if str(event["id"]) == str(id)), None)
    if event:
        return {"event": event}, 200
    else:
        return {"error": "Event not found"}, 404

@app.route("/students", methods=["GET"])
def get_students():
    return {"students": students}, 200

@app.route("/registrations", methods=["POST"])
def create_registration():
    data = request.get_json()
    new_registration = {
        "id": len(registrations) + 1,
        "student_id": data["student_id"],
        "event_id": data["event_id"],
        "status": "pending"     
    }
    registrations.append(new_registration)
    return {"message": "Registration created successfully"}, 201

@app.route("/registrations", methods=["GET"])
def get_registrations():
    return {"registrations": registrations}, 200

@app.route("/registrations/<id>", methods=["GET"])
def get_registration(id):
    id = request.args.get("id")
    if not id:
        return {"error": "Missing id parameter"}, 400
    registration = next((reg for reg in registrations if str(reg["id"]) == str(id)), None)
    if registration:
        return {"registration": registration}, 200
    else:
        return {"error": "Registration not found"}, 404

if __name__ == "__main__":
    app.run(debug=True)