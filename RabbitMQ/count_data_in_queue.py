import pika
import time

# RabbitMQ connection settings for Docker container on localhost
host = "localhost"
username = "guest"
password = "guest"
queue_name = "hello"  # Replace with your actual queue name

# File to log the queue lengths
log_file = "queue_lengths.txt"

# Create connection credentials and parameters
credentials = pika.PlainCredentials(username, password)
parameters = pika.ConnectionParameters(host=host, credentials=credentials)

# Function to get the queue length
def get_queue_length():
    try:
        # Establish a blocking connection to RabbitMQ
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Query the queue state (passively)
        queue_declare = channel.queue_declare(queue=queue_name, passive=True)
        message_count = queue_declare.method.message_count

        return message_count
    except pika.exceptions.ChannelClosedByBroker as e:
        print(f"Error: The queue '{queue_name}' does not exist or you do not have access. {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()

# Main loop to check queue length every second
try:
    while True:
        message_count = get_queue_length()
        if message_count is not None:
            # Print and log the result
            print(f"Messages remaining in the queue '{queue_name}': {message_count}")

            # Write to the log file
            with open(log_file, "a") as file:
                file.write(f"{time.ctime()} - Queue Length: {message_count}\n")
        
        # Sleep for 1 second before checking again
        time.sleep(1)
except KeyboardInterrupt:
    print("Process interrupted. Exiting...")
