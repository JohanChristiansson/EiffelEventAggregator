import os
import time
import psutil
import requests
import argparse
from dotenv import load_dotenv

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
#This should have been done in a better way, needs to be changed manually to the correct queue as is.
EI_QUEUE_URL = "http://localhost:15672/api/queues/%2F/eiffel.eiffelintelligence-artifact.messageQueue.durable"
ER_QUEUE_URL = "http://localhost:15672/api/queues/%2F/eiffel.eiffel-er.ERMessageConsumer.durable"
NEO4J_QUEUE_URL = "http://localhost:15672/api/queues/%2F/neo4j"

LOG_FILE = "resource_usage.csv"

def get_queue_length(url):
    try:
        response = requests.get(url, auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        return response.json().get("messages", 0)
    except requests.RequestException as e:
        print(f"Error fetching queue length: {e}")
        return None

def get_acknowledged_events(url):
    try:
        response = requests.get(url, auth=(USERNAME, PASSWORD))
        response.raise_for_status()
        return response.json().get("message_stats", {}).get("ack", 0)
    except requests.RequestException as e:
        print(f"Error fetching acknowledged events: {e}")
        return None

def get_disk_usage():
    usage = psutil.disk_usage('/')
    return usage.percent, usage.used / (1024**3), usage.free / (1024**3)

def get_memory_usage():
    memory = psutil.virtual_memory()
    return memory.percent, memory.used / (1024**3), memory.free / (1024**3)

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def write_log_header(neo4j_mode):
    if not os.path.exists(LOG_FILE):
        header = [
            "Timestamp", "Queue Length", "Events/Sec",
            "CPU Usage (%)", "Disk Usage (%)", "Disk Used (GB)", "Disk Free (GB)",
            "Memory Usage (%)", "Memory Used (GB)", "Memory Free (GB)"
        ]
        if not neo4j_mode:
            header[1] = "EI Queue Length"
            header[2] = "ER Queue Length"
            header.insert(3, "Events/Sec EI")
            header.insert(4, "Events/Sec ER")
        else:
            header[1] = "NEO Queue Length"
            header[2] = "Events/Sec NEO"
        with open(LOG_FILE, "w") as file:
            file.write(", ".join(header) + "\n")

def main():
    parser = argparse.ArgumentParser(description="RabbitMQ Queue Logger")
    parser.add_argument("--neo4j", action="store_true", help="Log only the NEO4J queue instead of both EI and ER queues")
    args = parser.parse_args()

    previous_ack_primary = previous_ack_secondary = None
    write_log_header(args.neo4j)

    try:
        while True:
            if args.neo4j:
                queue_url_primary = NEO4J_QUEUE_URL
                queue_name_primary = "NEO"
            else:
                queue_url_primary = EI_QUEUE_URL
                queue_name_primary = "EI"
                queue_url_secondary = ER_QUEUE_URL
                queue_name_secondary = "ER"

            message_count_primary = get_queue_length(queue_url_primary)
            ack_count_primary = get_acknowledged_events(queue_url_primary)
            events_per_sec_primary = max(0, ack_count_primary - previous_ack_primary) if previous_ack_primary is not None else 0
            previous_ack_primary = ack_count_primary

            log_data = [
                time.ctime(),
                f"{queue_name_primary} Queue Length: {message_count_primary}",
                f"Events/Sec {queue_name_primary}: {events_per_sec_primary}",
                f"CPU Usage: {get_cpu_usage()}%",
                f"Disk Usage: {get_disk_usage()[0]}%",
                f"Disk Used: {get_disk_usage()[1]:.2f} GB",
                f"Disk Free: {get_disk_usage()[2]:.2f} GB",
                f"Memory Usage: {get_memory_usage()[0]}%",
                f"Memory Used: {get_memory_usage()[1]:.2f} GB",
                f"Memory Free: {get_memory_usage()[2]:.2f} GB"
            ]

            if not args.neo4j:
                message_count_secondary = get_queue_length(queue_url_secondary)
                ack_count_secondary = get_acknowledged_events(queue_url_secondary)
                events_per_sec_secondary = max(0, ack_count_secondary - previous_ack_secondary) if previous_ack_secondary is not None else 0
                previous_ack_secondary = ack_count_secondary
                log_data.insert(2, f"{queue_name_secondary} Queue Length: {message_count_secondary}")
                log_data.insert(3, f"Events/Sec {queue_name_secondary}: {events_per_sec_secondary}")

            with open(LOG_FILE, "a") as file:
                file.write(", ".join(log_data) + "\n")

            print(", ".join(log_data))
            time.sleep(10)
    except KeyboardInterrupt:
        print("Process interrupted. Exiting...")

if __name__ == "__main__":
    main()
