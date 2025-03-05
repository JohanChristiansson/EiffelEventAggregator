"""

Script to connect to fetch events from RabbitMQ and insert them in Memgraph
Log performance and possibility to test trigger effects

"""
import pika, sys, os
from dotenv import load_dotenv
import json
from neo4j import GraphDatabase
import argparse
import time
import os
import matplotlib.pyplot as plt
import multiprocessing
import threading

# Neo4j connection details
MEMGRAPH_URI = "bolt://localhost:7687" # Port can change based on system
MEMGRAPH_USER = "neo4j"
MEMGRAPH_PASSWORD = "demodemo"

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")
QUEUE_NAME = os.getenv("QUEUE_NAME")
BASE_URL = os.getenv('EVENT_REPOSITORY_URL')

# Argument parser setup
parser = argparse.ArgumentParser(description="Configuration settings for event processing")

parser.add_argument("--mode", type=str, choices=["process", "thread", "single"], default="single", help="Execution mode: 'single' (single threaded), 'process' (multiprocessing) or 'thread' (multithreading)")
parser.add_argument("--num-workers", type=int, default=os.cpu_count(), help="Number of worker threads/processes (default: CPU cores)")
parser.add_argument("--u-interval", type=int, default=2, help="Time between updates in terminal and log file (seconds)")
parser.add_argument("--tr-test", type=bool, default=False, help="If triggers should be dynamically added/tested")
parser.add_argument("--eps-threshold", type=int, default=40, help="Threshold for triggers to be added or removed (events/sec)")
parser.add_argument("--lr", type=float, default=0.2, help="Learning rate for trigger inserts or removal (percentage decrease)")
parser.add_argument("--ta", type=int, default=200, help="Start amount to add or decrease in trigger test")
parser.add_argument("--amount-threshold", type=int, default=20000, help="Amount of events before changing number of triggers")

# Parse arguments
args = parser.parse_args()

MODE = args.mode                                # Insert mode (Multiprocess/Thread/Single)          (String)
NUM_WORKERS = args.num_workers                  # Number of workers in threading and multiprocess   (int    | amount)
UPDATE_INTERVAL = args.u_interval               # Time between updates in terminal and log file     (int    | sec)
TRIGGER_STRESS_TEST = args.tr_test              # If Triggers should be dynamically added / tested  (bool)
EPS_THRESHOLD = args.eps_threshold              # Threshold for triggers to be added or removed     (int    | events/sec)
LR  = args.lr                                   # Learning rate for trigger inserts or removal      (float  | % decrease)
TRIGGER_START_ADDITION_AMOUNT = args.ta         # Start amount to add or decrease in trigger test   (int    | amount)
AMOUNT_THRESHOLD = args.amount_threshold        # Amount events before changing number of triggers  (int    | amount)
print(args)

start_time = time.time()                        # Start time for EPS update each UPDATE_INTERVAL
start_u_time = time.time()                      # Start time for EPS update each AMOUNT_THRESHOLD
event_count = 0                                 # Event count for last UPDATE_INTERVAL                  #TODO: Should not be global (?)
tot_count = 0                                   # Event count for total events inserted this session    #TODO: Should not be global (?)
eps_history = []                                # History of EPS for later historical graph
node_count_history = []                         # History of amount of events for each eps_history
amount_inserted_since_trigger_update = 0        # Amount inserted since triggers updated last           #TODO: Should not be global (?)
total_triggers = 0                              # Total triggers active

trigger_addition_amount = TRIGGER_START_ADDITION_AMOUNT # TODO: Should not be global (?)

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
        """Inserts an event and its relationships in Memgraph."""

        check_query = """
        UNWIND $links AS link
        OPTIONAL MATCH (target:Event {id: link.target})  // Allows missing targets
        RETURN link.target AS target_id, target IS NOT NULL AS target_exists
        """

        # Run query with a parameterized list of links
        result = list(tx.run(check_query, links=event.get("links", [])))

        # Extract missing targets
        missing_targets = [record["target_id"] for record in result if not record["target_exists"]]

        # Handle missing targets
        if missing_targets:
            raise ValueError(f"Missing target nodes: {missing_targets}. Rolling back insert.")

        
        # Insert event node
        query = """
        MERGE (e:Event {id: $id})  
        SET e.type = $type,
            e.timestamp = $timestamp,
            e.jsonData = $jsonData
        """
        tx.run(query, 
            id=event["meta"]["id"], 
            type=event["meta"]["type"], 
            timestamp=event["meta"]["time"], 
            jsonData=json.dumps(event)  # Convert JSON to string manually
        )

        # Insert relationships
        for link in event.get("links", []):
            dynamic_query = f"""
            MATCH (source:Event {{id: $from_id}})
            MATCH (target:Event {{id: $target_id}})
            MERGE (source)-[:`{link['type']}`]->(target);
            """
            tx.run(dynamic_query, from_id=event["meta"]["id"], target_id=link["target"])

        #tx.commit()
        

    def insert_triggers(self, total_triggers, count, lr = 0.2):
        """Creates the specified number of APOC triggers."""
        with self.driver.session(database="system") as session:
            for i in range(count):
                trigger_name = f"event_trigger_{i + total_triggers}"
                query = """
                    CALL apoc.trigger.install(
                        'neo4j',
                        '{trigger_name}',
                        '
                        WITH [n IN $createdNodes WHERE n.type = "EiffelArtifactCreatedEvent" AND n.id = "{i}"] AS nodes
                        UNWIND nodes AS n
                        MATCH (n)-[:FLOW_CONTEXT]->(e:Event {{type: "EiffelFlowContextDefinedEvent"}})
                        CALL apoc.load.jsonParams(
                            "http://localhost:5000/event_ArtC",
                            {{`Content-Type`: "application/json"}},
                            apoc.convert.toJson({{ArtC: n.id, FCD: e.id}})
                        ) YIELD value
                        RETURN NULL
                        ',
                        {{phase: "afterAsync"}}
                    )
                    """.format(trigger_name=trigger_name, i=i+total_triggers)
                session.run(query)
            print(f"✅ Created {count} triggers.")
        total_triggers += int(count)
        count *= (1-lr)
        return total_triggers, int(count)
    
    def remove_triggers(self, total_triggers, count, lr = 0.2):
        """Removes the specified number of APOC triggers."""
        if total_triggers - count > 0:
            with self.driver.session(database="system") as session:
                for i in range(count):
                    trigger_name = f"event_trigger_{total_triggers - i - 1}"
                    session.run(f"CALL apoc.trigger.drop('{NEO4J_USER}',{trigger_name}')")
                print(f"❌ Removed {count} triggers.")
            total_triggers -= int(count)
            count *= (1-lr)
            return total_triggers, int(count)


# Read events from file
def read_events_from_file(filename):
    """Reads a valid JSON array from the file."""
    with open(filename, "r") as f:
        return json.load(f)



def consume_def():
    print(HOST, type(HOST))
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host = HOST, heartbeat=60))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_qos(prefetch_count=1)
    inserter = EventInserter(MEMGRAPH_URI, MEMGRAPH_USER, MEMGRAPH_PASSWORD)


    log_file = "memgraph_insert_speed.log"  # File to store EPS data


    def callback(ch, method, _, body):
        try:
            global event_count, tot_count, start_time
            event_data = json.loads(body.decode('utf-8'))
            inserter.insert_event(event_data)
            event_count += 1
            tot_count += 1

            # EPS calculation
            elapsed_time = time.time() - start_time
            if elapsed_time >= UPDATE_INTERVAL:
                eps = event_count / elapsed_time
                event_count = 0
                start_time = time.time()

                # Write EPS + Total Events to file every 60 seconds
                with open(log_file, "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}, {tot_count}, {eps:.2f} events/sec\n")

                clear_terminal()
                print(f"\r✅ {time.strftime('%Y-%m-%d %H:%M:%S')} | Total: {tot_count} | {eps:.2f} events/sec", end="", flush=True)
                
            ch.basic_ack(delivery_tag=method.delivery_tag) #Acknowledges that the new data has been handled
        except KeyboardInterrupt:
            print("Interrupted by user. Exiting...")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            raise
        except Exception as e:
            print("Error processing message:", e)
            # Negative acknowledge and requeue the message to retry later
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


    channel.basic_consume(queue = QUEUE_NAME, on_message_callback = callback, auto_ack = False)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


    channel.basic_consume(queue = QUEUE_NAME, on_message_callback = callback, auto_ack = False)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


def consume(worker_id):
    """
    Function to consume messages from RabbitMQ and insert into Neo4j.
    Each worker runs this function in parallel.
    """
    print(f"Worker {worker_id} started in {MODE} mode...")
    
    credentials = pika.PlainCredentials(USERNAME, PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=HOST, heartbeat=60))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)
    channel.basic_qos(prefetch_count=256)  # Ensure fair distribution of messages across workers
    
    inserter = EventInserter(MEMGRAPH_URI, MEMGRAPH_USER, MEMGRAPH_PASSWORD)

    event_count = 0
    start_time = time.time()

    def callback(ch, method, _, body):
        nonlocal event_count, start_time
        try:
            event_data = json.loads(body.decode('utf-8'))
            inserter.insert_event(event_data)
            ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge message
            
            event_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time >= 5:  # Every 5 seconds, print EPS
                eps = event_count / elapsed_time
                print(f"[{MODE.upper()}] Worker {worker_id} -> EPS: {eps:.2f} events/sec")
                event_count = 0
                start_time = time.time()
        except ValueError as e:  # Missing relationship target
           # print(f"❌ Requeuing event due to missing target: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        except KeyboardInterrupt:
            print(f"Worker {worker_id} interrupted by user. Exiting...")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            raise
        except Exception as e:
            print(f"Worker {worker_id} error processing message:", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)
    channel.start_consuming()

def run_processes():
    """Run multiple worker processes."""
    processes = []
    for i in range(NUM_WORKERS):
        p = multiprocessing.Process(target=consume, args=(i,))
        p.start()
        processes.append(p)
    
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("\n[!] Terminating workers...")
        for p in processes:
            p.terminate()
        sys.exit(0)

def run_threads():
    """Run multiple worker threads."""
    threads = []
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=consume, args=(i,))
        t.start()
        threads.append(t)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[!] Terminating threads...")
        sys.exit(0)

def run_default():
    while True:
        try:
            consume_def()
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

def main():
    if MODE == "process":
        run_processes()
    elif MODE == "thread":
        run_threads()
    elif MODE == "single":
        run_default()
    else:
        print("[!] Invalid mode. Use --mode process, --mode thread or --mode single.")

if __name__ == '__main__':
    main()