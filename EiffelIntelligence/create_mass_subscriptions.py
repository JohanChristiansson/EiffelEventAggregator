import json
import time
import bson
import os
from ids import ids  #List of ids that trigger the pattern in first 150 000 events

folder_name = "subscriptions"
os.makedirs(folder_name, exist_ok=True)

for index, unique_id in enumerate(ids, start=1):
    subscription = [
        {
            "aggregationtype": "eiffel-ei-artifact",
            "created": int(time.time() * 1000),
            "notificationMeta": "http://localhost:5000/eiffel/specific_id",
            "notificationType": "REST_POST",
            "restPostBodyMediaType": "application/json",
            "notificationMessageKeyValues": [
                {
                    "formkey": "",
                    "formvalue": "{parameter: [{ name: 'jsonparams', value : to_string(@) }]}"
                }
            ],
            "repeat": False,
            "requirements": [
                {
                    "conditions": [
                        {
                            "jmespath": f"id=='{unique_id}'"
                        }
                    ]
                }
            ],
            "subscriptionName": f"subscription{index}",
            "authenticationType": "NO_AUTH",
            "password": "",
            "ldapUserName": "",
            "notificationMessageKeyValuesAuth": [],
            "_id": {
                "$oid": str(bson.ObjectId())
            }
        }
    ]

    filename = os.path.join(folder_name, f"subscription{index}.json")

    with open(filename, "w") as f:
        json.dump(subscription, f, indent=2)

    print(f"Generated {filename}")
