############################################
#      Simulation code for creating an     #
#       Event Stream in Eiffel Fasion      #
#     Simulation done for Neo4j Desktop    #
############################################


import random
import time
from neo4j import GraphDatabase
import uuid
import datetime

# Neo4j connection details
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "demodemo"

# Define possible event types
EVENT_TYPES = [
    "EiffelContextDefinedEvent",
    "EiffelArtifactCreatedEvent",
    "EiffelArtifactPublishedEvent",
    "EiffelConfidenceLevelModified"
]

class EiffelStream:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_event(self, event_type):
        """Create a new Eiffel event and link it correctly."""
        event_id = str(uuid.uuid4())  # Generate a unique event ID
        event_time = datetime.datetime.now().isoformat()  # Timestamp

        with self.driver.session() as session:
            # Create the event and get its actual UUID from Neo4j
            created_uuid = session.write_transaction(
                self._create_event, event_id, event_type, event_time
            )

            # Find random existing events to link based on event type
            self._link_randomly(session, event_type, created_uuid)

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

    def _link_randomly(self, session, event_type, new_uuid):
        """Randomly links the new event to an existing event based on type-specific rules."""
        # Get a random existing event UUID
        existing_uuid = session.read_transaction(self._get_random_event_uuid)

        if existing_uuid:
            if event_type == "EiffelContextDefinedEvent":
                session.execute_write(self._link_event, existing_uuid, new_uuid, "CONTEXT_DEFINED")

            elif event_type == "EiffelArtifactCreatedEvent":
                session.execute_write(self._link_event, existing_uuid, new_uuid, "CONTEXT_DEFINED")

            elif event_type == "EiffelArtifactPublishedEvent":
                session.execute_write(self._link_event, existing_uuid, new_uuid, "ARTIFACT")

            elif event_type == "EiffelConfidenceLevelModified":
                session.execute_write(self._link_event, existing_uuid, new_uuid, "SUBJECT")

    @staticmethod
    def _get_random_event_uuid(tx):
        """Fetch a random event UUID from the database."""
        query = """
        MATCH (e:Event)
        RETURN e.id AS uuid
        ORDER BY rand()
        LIMIT 1
        """
        result = tx.run(query)
        record = result.single()
        return record["uuid"] if record else None

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

try:
    while True:
        # Pick a random event type
        event_type = random.choice(EVENT_TYPES)

        # Create the event and link it dynamically
        new_event_uuid = graph.add_event(event_type)
        print(f"✅ Created {event_type} with UUID {new_event_uuid}")

        # Wait for a few seconds before creating the next event
        time.sleep(random.uniform(1, 5))  # Random delay between 1 to 5 seconds

except KeyboardInterrupt:
    print("\n🛑 Stopping Eiffel event stream.")
    graph.close()
