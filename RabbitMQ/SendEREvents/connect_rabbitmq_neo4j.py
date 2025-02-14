#!/usr/bin/env python
import pika, sys, os
from dotenv import load_dotenv
import json

load_dotenv()

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
queue_name = os.getenv("QUEUE_NAME")
base_url = os.getenv('EVENT_REPOSITORY_URL')

def main():
    print(host, type(host))
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host = host, credentials = credentials))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    def callback(_, __, ___, body):
        event_data = json.loads(body.decode('utf-8'))
        print(event_data["meta"]["id"])
        print()

    channel.basic_consume(queue = queue_name, on_message_callback = callback, auto_ack = True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)