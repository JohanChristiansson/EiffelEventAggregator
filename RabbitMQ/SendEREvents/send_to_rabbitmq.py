import pika
from get_events import get_new_events
import json
import time
import math
import requests
import os
import argparse
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
single_queue = os.getenv("QUEUE_NAME")  #Single Queue
multiple_queues = os.getenv("QUEUE_NAMES").split(',')
multiple_queues = list(map(str.strip, multiple_queues))
base_url = os.getenv('EVENT_REPOSITORY_URL')
page_size = 100000

#Argument Parsing
parser = argparse.ArgumentParser(description="RabbitMQ Queue Writer")
group = parser.add_mutually_exclusive_group()
group.add_argument("-eiffel", action="store_true", help="Enable writing to multiple queues")
group.add_argument("-graphdb", action="store_true", help="Enable writing to a single queue")
args = parser.parse_args()

#Default behavior: Single queue if no argument is provided
use_multiple_queues = args.eiffel if args.eiffel else not args.graphdb

#Use the first queue for Eiffel? Should perhaps be a specific one, the one processed the slowest? Or just EI 
queue_to_check = multiple_queues[0] if use_multiple_queues else single_queue

def get_queue_length(passive_queue):
    """Return Queue Length"""
    return passive_queue.method.message_count

def publish_events(channel, new_events, queues):
    """Publish events to the appropriate RabbitMQ queues."""
    for event in new_events:
        event_json = json.dumps(event)
        for queue_name in queues:
            channel.basic_publish(exchange='', routing_key=queue_name, body=event_json)

def send_events_to_rabbit(channel, current_page, queues_to_use):
    """Fetch new events and send them to the appropriate RabbitMQ queues."""
    new_events = []

    while current_page > 0:
        passive_queue = channel.queue_declare(queue=queue_to_check, passive=True)
        queue_length = get_queue_length(passive_queue)

        if queue_length is not None:
            print(f"Messages remaining in the queue '{queue_to_check}': {queue_length}")

        # If the current queue is smaller than page size, add more data
        if queue_length > page_size:
            time.sleep(1)
            continue

        print("Retrieving new page", current_page)
        new_events = get_new_events(base_url, current_page, current_page + 1, page_size, new_events)
        current_page -= 1

        publish_events(channel, new_events, queues_to_use)

def main():
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, credentials=credentials))

    channel = connection.channel()
    queues_to_use = multiple_queues if use_multiple_queues else [single_queue]

    for queue_name in queues_to_use:
        print(f"Declaring queue: {queue_name}")
        channel.queue_declare(queue=queue_name, durable=True)

    response = requests.get(base_url)
    starting_page = math.ceil(response.json()["totalNumberItems"] / page_size)

    send_events_to_rabbit(channel, starting_page, queues_to_use)

    connection.close()


if __name__ == '__main__':
    main()
