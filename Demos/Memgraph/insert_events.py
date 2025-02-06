from neo4j import GraphDatabase
import json
import time
import matplotlib.pyplot as plt

# Memgraph connection details
MEMGRAPH_URI = "bolt://localhost:7687"
MEMGRAPH_AUTH = ("", "")  # No authentication by default
EVENT_FILE = "events_new.json"

class EventInserter:
    def __init__(self, uri, auth):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def insert_event_with_links(self, event):
        """Insert an event and its links in one transaction to ensure consistency."""
        with self.driver.session(database="memgraph") as session:
            session.execute_write(self._insert_event_with_links, event)

    @staticmethod
    def _insert_event_with_links(tx, event):
        """Cypher query to insert an event along with its links in a single transaction."""
        query = """
        MERGE (e:Event {id: $id})
        SET e.type = $type, e.time = $time
        """
        tx.run(query, id=event["id"], type=event["type"], time=event["time"])

        for link in event["links"]:
            link_query = f"""
            MATCH (from:Event {{id: $from_id}}), (to:Event {{id: $to_id}})
            MERGE (from)-[:{link["type"]}]->(to)
            """
            tx.run(link_query, from_id=event["id"], to_id=link["id"])

# Read events from file
def read_events_from_file(filename):
    """Reads a valid JSON array from the file."""
    with open(filename, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    inserter = EventInserter(MEMGRAPH_URI, MEMGRAPH_AUTH)

    events = read_events_from_file(EVENT_FILE)
    if not events:
        print("⚠️ No events found in file.")
    else:
        start_time = time.time()
        event_count = 0
        eps_history = []
        node_count_history = []
        update_interval = 2

        for i, event in enumerate(events, 1):
            inserter.insert_event_with_links(event)
            event_count += 1

            elapsed_time = time.time() - start_time
            if elapsed_time >= update_interval:
                eps = event_count / elapsed_time
                eps_history.append(eps)
                node_count_history.append(i)

                event_count = 0
                start_time = time.time()

                print(f"\r✅ Inserted {i}/{len(events)} events | {eps:.2f} events/sec", end="", flush=True)

        print("\n✅ All events inserted successfully.")

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
