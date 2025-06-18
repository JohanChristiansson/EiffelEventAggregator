#!/bin/bash

set -e


cleanup() {
	    echo "Error detected! Stopping Docker Compose..."
	        docker compose -f Eiffel/ArtC/docker-compose.yml down
		    exit 1
	    }

trap cleanup ERR INT
#add script to empty queue as first step

echo "Starting Docker Compose..."
docker compose -f Eiffel/ArtC/docker-compose.yml up -d

echo "Waiting for containers to be ready..."
sleep 60

echo "Add subscriptions"
python3 EiffelEventAggregator/EiffelIntelligence/add_subscriptions.py EiffelEventAggregator/EiffelIntelligence/ArtP_Subscription Artifact_Created --count 1

# Start background processes
echo "Start the server"
#python3 EiffelEventAggregator/Server/server.py &
pid_server=$!

echo "Start tracking metrics"
python3 EiffelEventAggregator/RabbitMQ/LogQueueData/log_queue_data.py &
pid_logger=$!

# Run message bus script and wait for it to complete
echo "Start sending events to Message bus"
python3 EiffelEventAggregator/RabbitMQ/SendEREvents/send_to_rabbitmq.py -graphdb -file

# When message bus script completes, stop the background processes
echo "Message bus script finished. Stopping background processes..."

kill $pid_server
kill $pid_logger

echo "Stopping Docker Compose..."
docker-compose -f Eiffel/ArtP/docker-compose.yml down

echo "All scripts finished."
