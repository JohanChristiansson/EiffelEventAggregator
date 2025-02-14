import random
import uuid
import time
import json
import datetime
from RabbitMQ.VerifyGraph.cycle_detection import check_for_cycles
from RabbitMQ.VerifyGraph.plot_dag import plot_graph_from_events
from collections import deque

# Define possible event types
EVENT_TYPES = [
    "EiffelFlowContextDefinedEvent",
    "EiffelArtifactCreatedEvent",
    "EiffelArtifactPublishedEvent",
    "EiffelConfidenceLevelModified"
]

created_events = []
linkable_events = deque(maxlen=1000)

def generate_event_json(event_type, event_uuid, links):
    """Generate the event JSON based on the given event type and generated UUID."""
    
    timestamp_ms = int(datetime.datetime.now().timestamp() * 1000)
    #timestamp_ms = str(len(created_events) * 1000)

    event_json = {
        "meta": {
            "time": timestamp_ms,
            "id": event_uuid,
            "version": "1.0.0",
            "type": event_type,
            "source": {
                "domainId": "" 
            }
        },
        "data": {
            "customData": [
                {
                    "value": "",
                    "key": "name"
                },
                {
                    "value": 0,
                    "key": "iteration"
                }
            ],
            "submitter": {
                "name": "",
                "email": "",
                "group": "",
                "id": ""
            },
            "gitIdentifier": {
                "commitId": "",
                "repoName": "",
                "branch": "",
                "repoUri": ""
            }
        },
        "links": links
    }

    #Used for generation for NEO4J and Memgraph before entire object is implemented
    # event_json = {
    #     "meta": {
    #         "time": timestamp_ms,
    #         "id": event_uuid,
    #         "type": event_type,
    #     },
    #     "links": links
    # }

    return json.dumps(event_json, indent=2)


def create_event():
    """Creates events as dummy data to verify pattern detection for limited patterns. 
        Might not be accurate to how the events work in eiffel but should be enough
        to verify that patterns can be detected."""
    event_type = random.choice(EVENT_TYPES)
    event_id = str(uuid.uuid4())

    links = []
    
    if event_type == "EiffelFlowContextDefinedEvent" or event_type == "EiffelArtifactCreatedEvent":
        num_links = random.randint(0, 2)
        for _ in range(num_links):
            context_events = [e for e in linkable_events if e["meta"]["type"] == "EiffelFlowContextDefinedEvent"]
            if context_events:  # Check if there are context events to link to
                target_event = random.choice(context_events)

                link = {
                    "id": target_event["meta"]["id"],  
                    "type": "CONTEXT_DEFINED" 
                }

                # link = {
                #     "target": target_event["meta"]["id"],  
                #     "type": "CONTEXT_DEFINED" 
                # }
                links.append(link)
                
    elif event_type == "EiffelArtifactPublishedEvent":
        # link to exactly one EiffelArtifactCreatedEvent if one exists
        artifact_events = [e for e in linkable_events if e["meta"]["type"] == "EiffelArtifactCreatedEvent"]
        if artifact_events:  # Check if there is an artifact event to link to
            artifact_event = random.choice(artifact_events)
            link = {
                "id": artifact_event["meta"]["id"],  # Must link to a single EiffelArtifactCreatedEvent
                "type": "ARTIFACT"
            }
            
            # link = {
            #     "target": artifact_event["meta"]["id"],  # Must link to a single EiffelArtifactCreatedEvent
            #     "type": "ARTIFACT"
            # }
            links.append(link)

            num_links = random.randint(0, 2)
            for _ in range(num_links):
                context_events = [e for e in linkable_events if e["meta"]["type"] == "EiffelFlowContextDefinedEvent"]
                if context_events:  # Ensure there are context events to link to
                    context_event = random.choice(context_events)
                    
                    link = {
                        "id": context_event["meta"]["id"],
                        "type": "CONTEXT_DEFINED"
                    }
                    # link = {
                    #     "target": context_event["meta"]["id"],
                    #     "type": "CONTEXT_DEFINED"
                    # }
                    links.append(link)

    elif event_type == "EiffelConfidenceLevelModified":
        if linkable_events:  
            subject_event = random.choice(linkable_events) 
            link = {
                "id": subject_event["meta"]["id"],  
                "type": "SUBJECT"
            }
            # link = {
            #     "target": subject_event["meta"]["id"],  
            #     "type": "SUBJECT"
            # }
            links.append(link)

            num_links = random.randint(0, 2)
            for _ in range(num_links):
                context_events = [e for e in linkable_events if e["meta"]["type"] == "EiffelFlowContextDefinedEvent"]
                if context_events:  
                    context_event = random.choice(context_events)
                    link = {
                        "id": context_event["meta"]["id"],  
                        "type": "CONTEXT_DEFINED"
                    }
                    # link = {
                    #     "target": context_event["meta"]["id"],
                    #     "type": "CONTEXT_DEFINED"
                    # }
                    links.append(link)

    # Generate the event as a JSON object
    event_json = generate_event_json(event_type, event_id, links)
    event_json = json.loads(event_json)
    
    created_events.append(event_json)  # Store the generated event in the list for future linking
    linkable_events.append(event_json)
    
    #print(f"✅ Created event: {event_json}")

def flatten_event(event):
    """Removes the 'meta' field and moves its contents to the top level."""
    if "meta" in event:
        flattened_event = {**event["meta"], **event}  # Merge meta fields into event
        del flattened_event["meta"]  # Remove the old 'meta' key
        return flattened_event
    return event  # Return as-is if 'meta' doesn't exist


if __name__ == "__main__":
    try:
        while 1000000 > len(created_events):
            create_event()
            #time.sleep(0.2) 
            if len(created_events) % 10000 == 0:
                print(len(created_events))

        
            OUTPUT_FILE = "events_new.json"
 
            with open(OUTPUT_FILE, "a") as f:
                event = flatten_event(created_events[len(created_events)-1])
                f.write(json.dumps(event) + ",\n")
        
        #Verify that it is a dag
        #print(created_events)
        #check_for_cycles(created_events)
        #plot_graph_from_events(created_events)


    except KeyboardInterrupt:
        print("\n🛑 Stopping event creation.")


