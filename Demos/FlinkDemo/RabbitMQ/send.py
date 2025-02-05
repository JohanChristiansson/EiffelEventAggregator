import pika
from generator import create_event, created_events
from plot_dag import plot_graph_from_events
import json
import time
import datetime

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()


event1 = {
        "meta": {
            "time": 1000,
            "id": 1,
            "version": "1.0.0",
            "type": "EiffelFlowContextDefinedEvent",
            "source": {
                "domainId": "" 
            }
        },
        "data": {
            "customData": [
                {
                    "value": "",
                    "key": "name"
                },
                {
                    "value": 0,
                    "key": "iteration"
                }
            ],
            "submitter": {
                "name": "",
                "email": "",
                "group": "",
                "id": ""
            },
            "gitIdentifier": {
                "commitId": "",
                "repoName": "",
                "branch": "",
                "repoUri": ""
            }
        },
        "links": []
    }


event2 = {
        "meta": {
            "time": 2000,
            "id": 2,
            "version": "1.0.0",
            "type": "EiffelFlowContextDefinedEvent",
            "source": {
                "domainId": "" 
            }
        },
        "data": {
            "customData": [
                {
                    "value": "",
                    "key": "name"
                },
                {
                    "value": 0,
                    "key": "iteration"
                }
            ],
            "submitter": {
                "name": "",
                "email": "",
                "group": "",
                "id": ""
            },
            "gitIdentifier": {
                "commitId": "",
                "repoName": "",
                "branch": "",
                "repoUri": ""
            }
        },
        "links": []
    }

event3 = {
        "meta": {
            "time": 3000,
            "id": 3,
            "version": "1.0.0",
            "type": "EiffelArtifactCreatedEvent",
            "source": {
                "domainId": "" 
            }
        },
        "data": {
            "customData": [
                {
                    "value": "",
                    "key": "name"
                },
                {
                    "value": 0,
                    "key": "iteration"
                }
            ],
            "submitter": {
                "name": "",
                "email": "",
                "group": "",
                "id": ""
            },
            "gitIdentifier": {
                "commitId": "",
                "repoName": "",
                "branch": "",
                "repoUri": ""
            }
        },
        "links": [{
                    "target": 1,  
                    "type": "CONTEXT_DEFINED" 
                }]
    }

event4 = {
        "meta": {
            "time": 4000,
            "id": 4,
            "version": "1.0.0",
            "type": "EiffelArtifactPublishedEvent",
            "source": {
                "domainId": "" 
            }
        },
        "data": {
            "customData": [
                {
                    "value": "",
                    "key": "name"
                },
                {
                    "value": 0,
                    "key": "iteration"
                }
            ],
            "submitter": {
                "name": "",
                "email": "",
                "group": "",
                "id": ""
            },
            "gitIdentifier": {
                "commitId": "",
                "repoName": "",
                "branch": "",
                "repoUri": ""
            }
        },
        "links": [{
                    "target": 2,  
                    "type": "CONTEXT_DEFINED" 
                },
                {
                    "target": 3,  
                    "type": "ARTIFACT" 
                }]
    }


hardcoded_events1 =  [event1, event2, event3, event4]
hardcoded_events2 = [event2, event1, event3, event4]
hardcoded_events3 = [event1, event3, event2, event4]
#This one should not work
hardcoded_events4 = [event4, event1, event2, event3]

for i in range(4):
    create_event()
    time.sleep(0.2) 

    test = {
    "id": "2",
    "type": "click",
    "timestamp": 1000,
    "links": []
    }
    test = json.dumps(test)

    hardcoded_events = hardcoded_events3
    hardcoded_events[i]["meta"]["time"] = int(time.mktime(datetime.datetime.strptime(datetime.datetime.now().isoformat(), "%Y-%m-%dT%H:%M:%S.%f").timetuple()) * 1000)
    event = json.dumps(hardcoded_events[i])
    #event = json.dumps(created_events[i])

    channel.queue_declare(queue='hello')
    event_data = json.loads(event)

    print(event_data['meta']['id'], event_data['meta']['type'], event_data['links'])

    channel.basic_publish(exchange='', routing_key='hello', body=event)
    #print(" [x] Sent '" + event + "'")
connection.close()
#plot_graph_from_events(created_events)







