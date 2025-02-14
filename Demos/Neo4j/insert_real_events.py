#################################################
#                                               #
#   Attempt at creating an inserter to neo4j    #
#               With real data                  #
#                                               #
#################################################


from neo4j import GraphDatabase
import json
import time
import os
import matplotlib.pyplot as plt

# Neo4j connection details
NEO4J_URI = "bolt://localhost:7691"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "demodemo"
EVENT_FILE = "events_new.json"

# Delay between each insert to simulate a real-time stream (seconds)
#EVENT_DELAY = 0.1 

def clear_terminal():
    """Clears the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")

class EventInserter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def insert_event(self, event):
        """Insert a single event and its relationships."""
        with self.driver.session() as session:
            session.execute_write(self._insert_event, event)

    @staticmethod
    def _insert_event(tx, event):
        """Inserts an event and its relationships using UNWIND for efficiency."""
        query = """
        MERGE (e:Event {id: $id})  
        SET e.type = $type,
            e.timestamp = $timestamp,
            e.jsonData = apoc.convert.toJson($jsonData)
        """
        tx.run(query, 
            id=event["meta"]["id"], 
            type=event["meta"]["type"], 
            timestamp=event["meta"]["time"], 
            jsonData=event)

        # Single Cypher query to create all relationships in one go
        link_query = """
        UNWIND $links AS link
        MATCH (source:Event {id: $from_id})
        MATCH (target:Event {id: link.target})
        MERGE (source)-[r:`RELATION` {type: link.type}]->(target)
        """
        tx.run(link_query, from_id=event["meta"]["id"], links=event.get("links", []))


# Read events from file
def read_events_from_file(filename):
    """Reads a valid JSON array from the file."""
    with open(filename, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    inserter = EventInserter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    events = read_events_from_file(EVENT_FILE)
    if not events:
        print("⚠️ No events found in file.")
    else:
        start_time = time.time()
        event_count = 0
        eps_history = []
        node_count_history = []
        update_interval = 2  # Update stats every 2 seconds

        for i, event in enumerate(events, 1):
            inserter.insert_event(event)
            event_count += 1

            # Simulate real-time stream delay
            #time.sleep(EVENT_DELAY)

            # Print real-time stats
            elapsed_time = time.time() - start_time
            if elapsed_time >= update_interval:
                eps = event_count / elapsed_time
                eps_history.append(eps)
                node_count_history.append(i)

                event_count = 0
                start_time = time.time()

                clear_terminal()
                print(f"\rInserted {i}/{len(events)} events | {eps:.2f} events/sec", end="", flush=True)

        print("\nAll events inserted successfully.")

    inserter.close()

    # Generate speed graph
    if len(node_count_history) > 1:
        plt.figure(figsize=(8, 5))
        plt.plot(node_count_history, eps_history, marker="o", linestyle="-")
        plt.xlabel("Total Nodes Inserted")
        plt.ylabel("Events Per Second (EPS)")
        plt.title("Event Insertion Speed Over Time")
        plt.grid(True)
        plt.show()
    else:
        print("⚠️ Not enough data to generate a meaningful plot.")
