import json
import requests
import os
import argparse

"""
To run this file, you need to provide correct folder with the 
    subscriptions and specify which endpoint to use as positional argument

    Example: 
    python add_subscriptions.py subscriptions Artifact_Created --count 5
"""

ENDPOINTS = {
    "Artifact_Created": "http://localhost:8051/subscriptions",
    "test2": "http://localhost:5000/test2",
    "test3": "http://localhost:5000/test3",
}

def send_subscription(file_path, endpoint_url):
    """Read and send the subscription file to the specified API endpoint."""

    with open(file_path, "r") as f:
        data = json.load(f)
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(endpoint_url, json=data, headers=headers)

    if response.status_code == 200:
        print(f"Successfully sent {file_path} to {endpoint_url}")
    else:
        print(f"Failed to send {file_path} to {endpoint_url}. Status code: {response.status_code}")

def send_files_in_folder(folder_path, selected_endpoints, count=None):
    """Send all JSON files in the specified folder to the selected endpoints."""
    
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    if count:
        files = files[:count]  # Limit the number of files sent

    for filename in files:
        file_to_send = os.path.join(folder_path, filename)
        for endpoint_name in selected_endpoints:
            if endpoint_name in ENDPOINTS:
                send_subscription(file_to_send, ENDPOINTS[endpoint_name])
            else:
                print(f"Warning: Endpoint '{endpoint_name}' not recognized.")

def main():
    parser = argparse.ArgumentParser(description="Send subscription files to multiple endpoints.")
    parser.add_argument("folder", help="The folder containing the subscription files.")
    parser.add_argument("endpoints", nargs='+', help="The endpoints to send the subscriptions to. Example: Artifact_Created test2")
    parser.add_argument("--count", type=int, help="Number of subscription files to send.", default=None)
    args = parser.parse_args()

    folder_path = args.folder
    selected_endpoints = args.endpoints
    count = args.count

    if os.path.isdir(folder_path):
        send_files_in_folder(folder_path, selected_endpoints, count)
    else:
        print(f"Error: The folder '{folder_path}' does not exist.")

if __name__ == "__main__":
    main()
