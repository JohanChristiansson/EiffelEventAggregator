import pika
from get_events import get_new_events
import json
import time
import math
import requests
import os
import argparse
from dotenv import load_dotenv
import gc
import gzip

load_dotenv()

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
single_queue = os.getenv("QUEUE_NAME")  #Queue for ER/EI
multiple_queues = os.getenv("QUEUE_NAMES").split(',')
multiple_queues = list(map(str.strip, multiple_queues))
base_url = os.getenv('EVENT_REPOSITORY_URL')
page_size = 10_000
FILE = "EiffelEventAggregator/RabbitMQ/SendEREvents/events.json.gz"

#Argument Parsing
parser = argparse.ArgumentParser(description="RabbitMQ Queue Writer")
sink_group = parser.add_mutually_exclusive_group()
sink_group.add_argument("-eiffel", action="store_true", help="Enable writing to multiple queues")
sink_group.add_argument("-graphdb", action="store_true", help="Enable writing to a single queue")
source_group = parser.add_mutually_exclusive_group()
source_group.add_argument("-er", action="store_true", help="Read ER data directly from the event repository")
source_group.add_argument("-file", action="store_true", help="Read ER data from file")
args = parser.parse_args()

use_multiple_queues = args.eiffel if args.eiffel else not args.graphdb

queue_to_check = single_queue


def connect_to_rabbitmq():
    """Establish a RabbitMQ connection with retry logic"""
    attempt = 1
    while True:
        try:
            print(f"Connecting to RabbitMQ (Attempt {attempt})...")
            credentials = pika.PlainCredentials(username, password)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=host, credentials=credentials, heartbeat=30
                )
            )

            channel = connection.channel()
            channel.exchange_declare(exchange='events_exchange', exchange_type='fanout', durable=True)

            queues_to_use = multiple_queues if use_multiple_queues else [single_queue]
            for queue_name in queues_to_use:
                channel.queue_declare(queue=queue_name, durable=True)
                channel.queue_bind(exchange='events_exchange', queue=queue_name)
            
            channel.queue_declare(queue=single_queue, durable=True)

            print(f"Connected to RabbitMQ! Queues setup: {queues_to_use}")
            return connection, channel

        except pika.exceptions.AMQPError as e:
            print(f"Connection failed: {e}")
            wait_time = min(2 ** attempt, 15)
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            attempt += 1

def get_queue_length(passive_queue):
    """Return Queue Length"""
    return passive_queue.method.message_count

def read_events_from_file(file_path, chunk_size = page_size):
    """Generator to read a large JSON file line by line, yielding chunks of events."""
    with gzip.open(file_path, "rt", encoding="utf-8") as f:
        chunk = []
        for line in f:
            try:
                event = json.loads(line.strip())
                chunk.append(event)
            except json.JSONDecodeError:
                print("Invalid line", event)
                continue  #Skip invalid lines, if any
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk  #Yield the last chunk if there are remaining events


def wait_for_queue_to_empty(channel, queue_name, threshold=0):
    """Wait until the queue has processed most of its messages."""
    #Set threshold to 0 to ensure all data is in ER before we start using EI
    while True:
        passive_queue = channel.queue_declare(queue=queue_name, passive=True)
        queue_length = passive_queue.method.message_count
        if queue_length <= threshold:
            break
        print(f"Waiting for {queue_name} to empty... ({queue_length} messages left)")
        time.sleep(2)

def publish_events(connection, channel, new_events):
    print("Start publishing events", len(new_events))
    """Publish events to RabbitMQ"""
    

    for event in new_events:
        event_json = json.dumps(event)
        while True:
            try:
                channel.basic_publish(exchange='', routing_key=single_queue, body=event_json)
                #print(event_json, "Publish to ER/GraphDB")
                break
            except (pika.exceptions.AMQPError, pika.exceptions.StreamLostError) as e:
                print(f"RabbitMQ error while publishing to ER: {e}, reconnecting...")
                time.sleep(5)
                connection, channel = connect_to_rabbitmq()

    wait_for_queue_to_empty(channel, single_queue)

    if not use_multiple_queues:
        return connection, channel

    for event in new_events:
        event_json = json.dumps(event)
        while True:
            try:
                channel.basic_publish(exchange='events_exchange', routing_key='', body=event_json)
                #print(event_json, "Publish to EI")
                break
            except (pika.exceptions.AMQPError, pika.exceptions.StreamLostError) as e:
                print(f"RabbitMQ error while publishing to exchange: {e}, reconnecting...")
                time.sleep(5)
                connection, channel = connect_to_rabbitmq()

    return connection, channel


def send_events_to_rabbit(connection, channel, current_page):
    """Fetch new events and send them to the appropriate RabbitMQ queues."""
    new_events = []
    file_index = 0
    current_time = time.time()

    if args.file:
        file_gen = read_events_from_file(FILE) 
    while current_page > 0:
        passive_queue = channel.queue_declare(queue=queue_to_check, passive=True)
        queue_length = get_queue_length(passive_queue)

        if queue_length is not None:
            print(f"Messages remaining in the queue '{queue_to_check}': {queue_length}")

        #If the current queue is smaller than page size, add more data
        if queue_length > page_size * 5:
            time.sleep(1)
            continue

        if args.er:
            print("Retrieving new page", current_page)
            new_events = get_new_events(base_url, current_page, current_page + 1, page_size, new_events)
            current_page -= 1

        if args.file: 
            print(f"Reading events from file, starting from index {file_index}")
            try:
                new_events = next(file_gen)
                file_index += page_size
            except StopIteration:
                print("End of file reached.")
                break

        t = time.time()
        print("Start publishing events")
        connection, channel = publish_events(connection, channel, new_events)
        print("Finish publishing events",time.time() - t)
        print("Current page took in total", time.time() - current_time)
        current_time = time.time()
    return connection

def main(): 
    connection, channel = connect_to_rabbitmq()

    response = requests.get(base_url)
    starting_page = math.ceil(response.json()["totalNumberItems"] / page_size)

    #Return connection if it was changed. 
    connection = send_events_to_rabbit(connection, channel, starting_page)

    connection.close()


if __name__ == '__main__':
    main()


