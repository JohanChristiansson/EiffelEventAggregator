############################################
#      Simulation code for creating an     #
#       Event Stream in Eiffel Fashion     #
#     Simulation done for Neo4j Desktop    #
############################################


import random
import time
from neo4j import GraphDatabase
import uuid
import datetime
import matplotlib.pyplot as plt
import os

# Neo4j connection details
NEO4J_URI = "bolt://localhost:7690"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "demodemo"

# Define possible event types
EVENT_TYPES = [
    "EiffelContextDefinedEvent",
    "EiffelArtifactCreatedEvent",
    "EiffelArtifactPublishedEvent",
    "EiffelConfidenceLevelModified"
]
Aaa = 0

class EiffelStream:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_event(self, event_type, prints=False):
        """Create a new Eiffel event and link it correctly."""
        event_id = str(uuid.uuid4())  # Generate a unique event ID
        event_time = datetime.datetime.now().isoformat()  # Timestamp

        with self.driver.session() as session:
            # Create the event and get its actual UUID from Neo4j
            created_uuid = session.execute_write(
                self._create_event, event_id, event_type, event_time
            )

            # Find random existing events to link based on event type
            self._link_randomly(session, event_type, created_uuid, prints)

        return created_uuid  # Return UUID for further linking

    @staticmethod
    def _create_event(tx, event_id, event_type, event_time):
        """Cypher query to insert the event and return its UUID."""
        query = """
        CREATE (e:Event {id: $event_id, type: $event_type, time: $event_time})
        RETURN e.id AS uuid
        """
        result = tx.run(query, event_id=event_id, event_type=event_type, event_time=event_time)
        return result.single()["uuid"]

    def _link_randomly(self, session, event_type, new_uuid, prints = False):
        """Links the newly created event to existing events based on the exact Eiffel specification."""

        if event_type == "EiffelContextDefinedEvent":
            # Optional: Can link to previous ContextDefined events
            num_links = random.randint(0, 2)  
            context_events = session.execute_read(self._get_multiple_random_event_uuids, new_uuid, "EiffelContextDefinedEvent", num_links)
            for existing_uuid, existing_type in context_events:
                session.execute_write(self._link_event, new_uuid, existing_uuid, "CONTEXT_DEFINED")
                if prints:
                    print(f"🔗 Linked {new_uuid} ({event_type}) → {existing_uuid} ({existing_type}) via CONTEXT_DEFINED")

        elif event_type == "EiffelArtifactCreatedEvent":
            # Optional: Can link to previous ContextDefined events
            num_links = random.randint(0, 2)  
            context_events = session.execute_read(self._get_multiple_random_event_uuids, new_uuid, "EiffelContextDefinedEvent", num_links)
            for existing_uuid, existing_type in context_events:
                global Aaa
                session.execute_write(self._link_event, new_uuid, existing_uuid, "CONTEXT_DEFINED")
                Aaa = Aaa + 1
                if prints:
                    print(f"🔗 Linked {new_uuid} ({event_type}) → {existing_uuid} ({existing_type}) via CONTEXT_DEFINED")

        elif event_type == "EiffelArtifactPublishedEvent":
            # **MUST** link to exactly **one** EiffelArtifactCreatedEvent
            artifact_event = session.execute_read(self._get_random_event_uuid, new_uuid, "EiffelArtifactCreatedEvent")
            if not artifact_event[0]:
                if prints:
                    print(f"⚠️ ERROR: No EiffelArtifactCreatedEvent found for {new_uuid} ({event_type}). Cannot create orphan.")
                return  # Skip event creation if no valid link exists
            session.execute_write(self._link_event, new_uuid, artifact_event[0], "ARTIFACT")
            if prints:
                print(f"🔗 Linked {new_uuid} ({event_type}) → {artifact_event[0]} (EiffelArtifactCreatedEvent) via ARTIFACT")

            # **Optional:** Can also link to multiple ContextDefined events
            num_links = random.randint(0, 2)
            context_events = session.execute_read(self._get_multiple_random_event_uuids, new_uuid, "EiffelContextDefinedEvent", num_links)
            for existing_uuid, existing_type in context_events:
                session.execute_write(self._link_event, new_uuid, existing_uuid, "CONTEXT_DEFINED")
                if prints:
                    print(f"🔗 Linked {new_uuid} ({event_type}) → {existing_uuid} ({existing_type}) via CONTEXT_DEFINED")

        elif event_type == "EiffelConfidenceLevelModified":
            # **MUST** link to at least **one** event (any type)
            subject_event = session.execute_read(self._get_random_event_uuid, new_uuid, None)
            if not subject_event[0]:
                if prints:    
                    print(f"⚠️ ERROR: No existing event found for {new_uuid} ({event_type}). Cannot create orphan.")
                return  # Skip event creation if no valid link exists
            session.execute_write(self._link_event, new_uuid, subject_event[0], "SUBJECT")
            if prints:
                print(f"🔗 Linked {new_uuid} ({event_type}) → {subject_event[0]} ({subject_event[1]}) via SUBJECT")

            # **Optional:** Can also link to multiple ContextDefined events
            num_links = random.randint(0, 2)
            context_events = session.execute_read(self._get_multiple_random_event_uuids, new_uuid, "EiffelContextDefinedEvent", num_links)
            for existing_uuid, existing_type in context_events:
                session.execute_write(self._link_event, new_uuid, existing_uuid, "CONTEXT_DEFINED")
                if prints:
                    print(f"🔗 Linked {new_uuid} ({event_type}) → {existing_uuid} ({existing_type}) via CONTEXT_DEFINED")




    @staticmethod
    def _get_multiple_random_event_uuids(tx, exclude_uuid=None, event_type=None, limit=1):
        """Fetch multiple random event UUIDs ensuring they are not the same as `exclude_uuid`."""
        query = """
        MATCH (e:Event)
        WHERE ($exclude_uuid IS NULL OR e.id <> $exclude_uuid)
        AND ($event_type IS NULL OR e.type = $event_type)
        RETURN e.id AS uuid, e.type AS type
        ORDER BY rand()
        LIMIT $limit
        """
        result = tx.run(query, exclude_uuid=exclude_uuid, event_type=event_type, limit=limit)
        return [(record["uuid"], record["type"]) for record in result] if result else []


    @staticmethod
    def _get_random_event_uuid(tx, exclude_uuid=None, event_type=None):
        """Fetch a random event UUID from the database, ensuring it is not the same as `exclude_uuid`."""
        query = """
        MATCH (e:Event)
        WHERE ($exclude_uuid IS NULL OR e.id <> $exclude_uuid)
        AND ($event_type IS NULL OR e.type = $event_type)
        RETURN e.id AS uuid, e.type AS type
        ORDER BY rand()
        LIMIT 1
        """
        result = tx.run(query, exclude_uuid=exclude_uuid, event_type=event_type)
        record = result.single()
        return (record["uuid"], record["type"]) if record else (None, None)


    @staticmethod
    def _link_event(tx, from_uuid, to_uuid, relationship_type):
        """Creates a relationship between two events if both exist."""
        query = f"""
        MATCH (from:Event {{id: $from_uuid}}), (to:Event {{id: $to_uuid}})
        MERGE (from)-[r:{relationship_type}]->(to)
        RETURN r
        """
        tx.run(query, from_uuid=from_uuid, to_uuid=to_uuid)


# Start streaming Eiffel events continuously
graph = EiffelStream(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

def clear_terminal():
    """Clears the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")  # Windows: cls | Linux/Mac: clear

# Tracking data
event_count = 0
start_time = time.time()
update_interval = 2

eps_history = []  # Speed values (Y-axis)
node_count_history = []  # Total nodes appended (X-axis)
total_nodes = 0  

try:
    while True:
        # Pick a random event type
        event_type = random.choice(EVENT_TYPES)

        # Create the event and link it dynamically
        new_event_uuid = graph.add_event(event_type)

        # Increment event counters
        event_count += 1
        total_nodes += 1

        # Measure elapsed time
        elapsed_time = time.time() - start_time
        if elapsed_time >= update_interval:
            # Compute events per second (EPS)
            eps = event_count / elapsed_time

            # Store data for plotting
            eps_history.append(eps)
            node_count_history.append(total_nodes)

            clear_terminal()

            # Print real-time speed (without clutter)
            print(f"\rEvents per second: {eps:.2f} EPS | Total Nodes: {total_nodes}", end="", flush=True)

            # Reset counters
            event_count = 0
            start_time = time.time()

        # Wait before creating the next event
        #time.sleep(0.2)

except KeyboardInterrupt:
    print("\n🛑 Stopping Eiffel event stream...")

finally:
    graph.close()
    print("\nNeo4j connection closed.")

    # Check if there's data to plot
    if len(node_count_history) > 1:
        print("Generating the speed plot...")

        # Plot the graph
        plt.figure(figsize=(8, 5))
        plt.plot(node_count_history, eps_history, marker="o", linestyle="-")
        plt.xlabel("Total Nodes Appended")
        plt.ylabel("Speed (Events Per Second)")
        plt.title("Event Append Speed Over Time")
        plt.grid(True)

        # Ensure the plot stays open
        plt.show(block=True)
    else:
        print("Not enough data to generate a meaningful plot.")


