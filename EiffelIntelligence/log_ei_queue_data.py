import os
import time
import psutil
import requests
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
RABBITMQ_API_URL = "http://localhost:15672/api/queues/%2F/eiffel.eiffelintelligence-artifact.messageQueue.durable"

log_file = "resource_usage.csv"

def get_queue_length():
    """Fetch the current number of messages in the queue."""
    try:
        response = requests.get(RABBITMQ_API_URL, auth=(USERNAME, PASSWORD))
        if response.status_code == 200:
            queue_data = response.json()
            return queue_data.get("messages", 0)
        else:
            print(f"Error: Unable to fetch queue data. HTTP Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching queue length: {e}")
        return None

def get_acknowledged_events():
    """Fetch the total number of acknowledged messages."""
    try:
        response = requests.get(RABBITMQ_API_URL, auth=(USERNAME, PASSWORD))
        if response.status_code == 200:
            queue_data = response.json()
            return queue_data.get("message_stats", {}).get("ack", 0)
        else:
            print(f"Error: Unable to fetch acknowledged messages. HTTP Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching acknowledged events: {e}")
        return None

def get_disk_usage():
    """Fetch disk usage statistics."""
    usage = psutil.disk_usage('/')
    return usage.percent, usage.used, usage.free

def get_memory_usage():
    """Fetch memory usage statistics."""
    memory = psutil.virtual_memory()
    return memory.percent, memory.used, memory.free

def get_cpu_usage():
    """Fetch CPU usage percentage."""
    return psutil.cpu_percent(interval=1)

def main():
    previous_ack_count = None

    # Write header to the CSV log file if it doesn't exist
    if not os.path.exists(log_file):
        with open(log_file, "w") as file:
            file.write(
                "Timestamp,Queue Length,Acknowledged Events/Sec,CPU Usage (%),Disk Usage (%),Disk Used (GB),Disk Free (GB),Memory Usage (%),Memory Used (GB),Memory Free (GB)\n"
            )

    try:
        while True:
            message_count = get_queue_length()
            current_ack_count = get_acknowledged_events()

            acknowledged_per_second = 0
            if previous_ack_count is not None and current_ack_count is not None:
                acknowledged_per_second = max(0, current_ack_count - previous_ack_count)

            previous_ack_count = current_ack_count

            cpu_usage = get_cpu_usage()
            disk_usage_percent, disk_used, disk_free = get_disk_usage()
            memory_usage_percent, memory_used, memory_free = get_memory_usage()

            # Create a CSV formatted log entry using str.format
            # log_entry = "{},{},{},{},{},{:.2f},{:.2f},{},{:.2f},{:.2f}\n".format(
            #     time.ctime(),
            #     message_count,
            #     acknowledged_per_second,
            #     cpu_usage,
            #     disk_usage_percent,
            #     disk_used / (1024**3),
            #     disk_free / (1024**3),
            #     memory_usage_percent,
            #     memory_used / (1024**3),
            #     memory_free / (1024**3)
            # )
            log_entry = f"{time.ctime()}, " \
            f"Queue Length: {message_count}, " \
            f"Events/Sec: {acknowledged_per_second}, " \
            f"CPU Usage: {cpu_usage}%, " \
            f"Disk Usage: {disk_usage_percent}%, " \
            f"Disk Used: {disk_used / (1024**3):.2f} GB, " \
            f"Disk Free: {disk_free / (1024**3):.2f} GB, " \
            f"Memory Usage: {memory_usage_percent}%, " \
            f"Memory Used: {memory_used / (1024**3):.2f} GB, " \
            f"Memory Free: {memory_free / (1024**3):.2f} GB\n"




            # Append the log entry to the CSV file
            with open(log_file, "a") as file:
                file.write(log_entry)

            # Print the log entry to console
            print(log_entry.strip())

            time.sleep(10)  # Log every 10 seconds

    except KeyboardInterrupt:
        print("Process interrupted. Exiting...")

if __name__ == "__main__":
    main()
