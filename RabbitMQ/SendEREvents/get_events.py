import requests
import json
import time
import math
from dotenv import load_dotenv
import os
import gzip

load_dotenv()
num_events = 0
prev_num_events = 0

def fetch_page(url, page_no, page_size, max_retries=100):
    full_url = f"{url}?pageNo={page_no}&pageSize={page_size}"
    attempt = 1
    while attempt <= max_retries:
        try:
            print(full_url)
            response = requests.get(full_url)
            response.raise_for_status()
            return response.json()["items"], response.json()["totalNumberItems"]
        except (requests.RequestException, ValueError) as e:
            print(f"Attempt {attempt} failed for page {page_no}: {e}")
            time.sleep(min(2 ** attempt, 30))
            attempt += 1
    print(f"Failed to fetch page {page_no} after {max_retries} attempts")
    return [], 0


def get_new_events(url, newer_page_no, older_page_no, page_size, previous_page_data):
    global prev_num_events
    global num_events

    combined = []

    newer_events, num_events = fetch_page(url, newer_page_no, page_size)
    #If no new events were added no need to check previous page
    #
    if num_events - prev_num_events > page_size and prev_num_events != 0:
        print("Number of new events were more than an entire page size. Might have missed some events. This will most likely never happen", num_events, prev_num_events)
    if (num_events == prev_num_events) or (prev_num_events == 0):
        prev_num_events = num_events
        for event in reversed(newer_events):
            combined.append(event)
        return combined
    prev_num_events = num_events
    
    #Only do this if total num of events has increased
    older_events, _ = fetch_page(url, older_page_no, page_size)
    #Get the events that shifted down a page
    previous_ids = {event["meta"]["id"] for event in previous_page_data}
    older_events = [event for event in older_events if event["meta"]["id"] not in previous_ids]

    for event in reversed(older_events):
        combined.append(event)
    for event in reversed(newer_events):
        combined.append(event)
    return list({event["meta"]["id"]: event for event in combined}.values())

def fetch_all_events(url, starting_page, page_size, output_file = "events.json"):
    #all_events = []
    current_page = starting_page
    new_events = []
    with gzip.open("events.json.gz", "wt", encoding="utf-8") as f:

    #Process pages moving upward toward page 1 (newer events)
        while current_page > 0:
            print("Retrieving new page", current_page)
            #New events is the events from last query
            new_events = get_new_events(url, current_page, current_page + 1, page_size, new_events)
            current_page = current_page - 1
            #all_events = new_events + all_events
            for event in new_events:
                    f.write(json.dumps(event) + "\n")
    
    return []#all_events

if __name__ == '__main__':
    page_size = 100000
    base_url = os.getenv('EVENT_REPOSITORY_URL')

    response = requests.get(base_url)
    
    starting_page = math.ceil(response.json()["totalNumberItems"]/page_size)
    print(starting_page)
    
    events = fetch_all_events(base_url, starting_page, page_size)
    #event_ids = [event["meta"]["id"] for event in events]
    #print(f"\nTotal events fetched: {len(event_ids)}", len(set(event_ids)), len(events))