import json
import uuid
import datetime
import time
import random

# Define possible event types
EVENT_TYPES = [
    "EiffelContextDefinedEvent",
    "EiffelArtifactCreatedEvent",
    "EiffelArtifactPublishedEvent",
    "EiffelConfidenceLevelModified"
]

OUTPUT_FILE = "events.json"
existing_events = []  # Store existing events for linking

def generate_event():
    """Generate an event with correct links and write it to a file with valid JSON format."""
    event_id = str(uuid.uuid4())  # Generate a unique event ID
    event_type = random.choice(EVENT_TYPES)
    event_time = timestamp_ms = int(time.mktime(datetime.datetime.strptime(event_time, "%Y-%m-%dT%H:%M:%S.%f").timetuple()) * 1000)
   # Timestamp

    event_data = {
        "id": event_id,
        "type": event_type,
        "time": event_time,
        "links": []  # Store linked event IDs with correct relationship types
    }

    # Define links based on event type
    if event_type == "EiffelContextDefinedEvent":
        num_links = random.randint(0, 2)
        context_events = [e for e in existing_events if e["type"] == "EiffelContextDefinedEvent"]
        for linked_event in random.sample(context_events, min(len(context_events), num_links)):
            event_data["links"].append({"id": linked_event["id"], "type": "CONTEXT_DEFINED"})

    elif event_type == "EiffelArtifactCreatedEvent":
        num_links = random.randint(0, 2)
        context_events = [e for e in existing_events if e["type"] == "EiffelContextDefinedEvent"]
        for linked_event in random.sample(context_events, min(len(context_events), num_links)):
            event_data["links"].append({"id": linked_event["id"], "type": "CONTEXT_DEFINED"})

    elif event_type == "EiffelArtifactPublishedEvent":
        artifact_events = [e for e in existing_events if e["type"] == "EiffelArtifactCreatedEvent"]
        if artifact_events:
            linked_event = random.choice(artifact_events)
            event_data["links"].append({"id": linked_event["id"], "type": "ARTIFACT"})
        
        num_links = random.randint(0, 2)
        context_events = [e for e in existing_events if e["type"] == "EiffelContextDefinedEvent"]
        for linked_event in random.sample(context_events, min(len(context_events), num_links)):
            event_data["links"].append({"id": linked_event["id"], "type": "CONTEXT_DEFINED"})

    elif event_type == "EiffelConfidenceLevelModified":
        if existing_events:
            linked_event = random.choice(existing_events)
            event_data["links"].append({"id": linked_event["id"], "type": "SUBJECT"})
        
        num_links = random.randint(0, 2)
        context_events = [e for e in existing_events if e["type"] == "EiffelContextDefinedEvent"]
        for linked_event in random.sample(context_events, min(len(context_events), num_links)):
            event_data["links"].append({"id": linked_event["id"], "type": "CONTEXT_DEFINED"})

    # Store the event for future linking
    existing_events.append(event_data)

    # Append event to file in JSON format (newline-separated)
    with open(OUTPUT_FILE, "a") as f:
        f.write(json.dumps(event_data) + ",\n")

    #print(f"📄 Event written to file: {event_data}")

try:
    for i in range(20000):
        generate_event()
except KeyboardInterrupt:
    print("\n🛑 Stopping event generation.")
