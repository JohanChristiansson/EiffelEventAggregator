from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/trigger-alert', methods=['POST'])
def trigger_alert():
    data = request.json
    print(data)
    event_id = data.get("eventId")
    context_id = data.get("contextId")

    if context_id != "NONE":
        print(f"ALERT: ArtifactCreatedEvent {event_id} is linked to ContextDefinedEvent {context_id}")
    else:
        print(f"ALERT: ArtifactCreatedEvent {event_id} has NO context-defined link")

    return jsonify({"status": "alert received"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001)