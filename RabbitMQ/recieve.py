#!/usr/bin/env python
import pika, sys, os
from dotenv import load_dotenv

load_dotenv()


def main():
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    credentials = pika.PlainCredentials(username, password)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue='neo4j')

    def callback(ch, method, properties, body):
        print(f" [x] Received {body}")

    channel.basic_consume(queue='neo4j', on_message_callback=callback, auto_ack=True)

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




