import pika
from get_events import get_new_events
import json
import time
import math
import requests
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
queue = os.getenv("QUEUE_NAME") #queue to check for adding new elements
multiple_queues = os.getenv("QUEUE_NAMES").split(',')
multiple_queues = list(map(str.strip, multiple_queues))
base_url = os.getenv('EVENT_REPOSITORY_URL')
page_size = 100000


# Function to get the queue length
def get_queue_length(passive_queue):
    message_count = passive_queue.method.message_count
    return message_count

#Main loop to check queue length every second
def send_events_to_rabbit(channel, current_page):
    new_events = []

    while current_page > 0:
        passive_queue = channel.queue_declare(queue=queue, passive=True)
        queue_length = get_queue_length(passive_queue)
        if queue_length is not None:
            print(f"Messages remaining in the queue '{queue}': {queue_length}")

        #If the current queue is smaller than page size, add more data to the queue
        if queue_length > page_size:
            time.sleep(1)
            continue

        print("Retrieving new page", current_page)
        #New events is the events from last query
        new_events = get_new_events(base_url, current_page, current_page + 1, page_size, new_events)
        current_page = current_page - 1
        print(len(new_events))
        for event in new_events:
            event = json.dumps(event)
            for queue_name in multiple_queues:
                channel.basic_publish(exchange='', routing_key=queue_name, body=event)

if __name__ == '__main__':
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host, credentials=credentials))

    print(multiple_queues)
    channel = connection.channel()
    for queue_name in multiple_queues:
        print(queue_name)
        channel.queue_declare(queue=queue_name, durable=True)
    exit   
    
    response = requests.get(base_url)
    starting_page = math.ceil(response.json()["totalNumberItems"]/page_size)

    send_events_to_rabbit(channel, starting_page)


    connection.close()









