"""import pika
from generator import create_event, created_events
from plot_dag import plot_graph_from_events
import json
import time

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()


for i in range(10):
    create_event()
    time.sleep(0.2) 

    test = {
    "id": "2",
    "type": "click",
    "timestamp": 1000,
    "links": []
    }
    test = json.dumps(test)

    event = json.dumps(created_events[i])

    channel.queue_declare(queue='hello')
    event_data = json.loads(event)

    print(event_data['meta']['id'], event_data['meta']['type'], event_data['links'])

    channel.basic_publish(exchange='', routing_key='hello', body=event)
    #print(" [x] Sent '" + event + "'")
connection.close()
plot_graph_from_events(created_events)"""

import pika
import json
import time
from plot_dag import plot_graph_from_events

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# List of predefined events
events = [
    {"id": "1", "type": "gul", "timestamp": 1000, "links": []},
    {"id": "2", "type": "scroll", "timestamp": 2000, "links": ["1"]},
    {"id": "3", "type": "click", "timestamp": 3000, "links": ["2"]},
    {"id": "4", "type": "click", "timestamp": 4000, "links": ["2"]},
    {"id": "5", "type": "purchase", "timestamp": 5000, "links": ["1", "2"]},
    {"id": "6", "type": "scroll", "timestamp": 6000, "links": []}
]

created_events = []  # Store sent events

channel.queue_declare(queue='hello')

for event in events:
   # time.sleep(0.2)  # Simulate delay

    event_json = json.dumps(event)
    created_events.append(event)

    event_data = json.loads(event_json)
   # print(event_data['id'], event_data['type'], event_data['links'])

    channel.basic_publish(exchange='', routing_key='hello', body=event_json)

connection.close()







