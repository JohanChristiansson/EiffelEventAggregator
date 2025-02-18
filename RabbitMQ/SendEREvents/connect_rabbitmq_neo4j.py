#!/usr/bin/env python
import pika, sys, os
from dotenv import load_dotenv
import json
from neo4j import GraphDatabase
import time
import os
import matplotlib.pyplot as plt

# Neo4j connection details
NEO4J_URI = "bolt://localhost:7691"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "demodemo"

load_dotenv()

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
queue_name = os.getenv("QUEUE_NAME")
base_url = os.getenv('EVENT_REPOSITORY_URL')

start_time = time.time()
event_count = 0
tot_count = 0
eps_history = []
node_count_history = []
update_interval = 2

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
        #print("a")
        # Single Cypher query to create all relationships in one go
        link_query = """
        UNWIND $links AS link
        MATCH (source:Event {id: $from_id})
        MATCH (target:Event {id: link.target})
        CALL apoc.create.relationship(source, link.type, {}, target) YIELD rel
        RETURN rel;
        """
        tx.run(link_query, from_id=event["meta"]["id"], links=event.get("links", []))


# Read events from file
def read_events_from_file(filename):
    """Reads a valid JSON array from the file."""
    with open(filename, "r") as f:
        return json.load(f)


def consume():
    print(host, type(host))
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host = host, heartbeat=60))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    inserter = EventInserter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    def callback(ch, method, _, body):
        try:
            global event_count, tot_count, start_time
            event_data = json.loads(body.decode('utf-8'))
            inserter.insert_event(event_data)
            event_count += 1
            tot_count += 1
            #print(event_data["meta"]["id"])

            # EPS calculation
            elapsed_time = time.time() - start_time
            if elapsed_time >= update_interval:
                eps = event_count / elapsed_time
                event_count = 0
                start_time = time.time()

                clear_terminal()
                print(f"\r✅ Processed {tot_count} events | {eps:.2f} events/sec", end="", flush=True)
            ch.basic_ack(delivery_tag=method.delivery_tag) #Acknowledges that the new data has been handled
        except KeyboardInterrupt:
            print("Interrupted by user. Exiting...")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            raise
        except Exception as e:
            print("Error processing message:", e)
            # Negative acknowledge and requeue the message to retry later
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


    channel.basic_consume(queue = queue_name, on_message_callback = callback, auto_ack = False)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

def main():
    while True:
        try:
            consume()
        except pika.exceptions.AMQPConnectionError as e:
            print("Connection error:", e, "Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("Interrupted by user. Exiting...")
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        except Exception as e:
            print("Unexpected error:", e)
            time.sleep(5)

if __name__ == '__main__':
    main()