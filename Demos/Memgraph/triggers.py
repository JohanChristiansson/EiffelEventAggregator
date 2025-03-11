import requests
import mgp


@mgp.read_proc
def send_http_request_artifact_created(
    ArtC: str, FCD: str
) -> mgp.Record(response=str):
    """
    Sends an HTTP request when an EiffelArtifactCreatedEvent is triggered.
    """
    url = "http://172.25.45.203:5000/event_ArtC"  # Use 'host.docker.internal' for Docker
    headers = {"Content-Type": "application/json"}
    payload = {"ArtC": ArtC, "FCD": FCD}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error if the request fails
        return mgp.Record(response=response.text)
    except requests.exceptions.RequestException as e:
        return mgp.Record(response=str(e))  # Return error message if the request fails


@mgp.read_proc
def send_http_request_artifact_published(ArtP: str, ArtC: str, FCD1: str, FCD2: str) -> mgp.Record():
    """Sends an HTTP request when an EiffelFlowContextDefinedEvent is created."""
    url = "http://localhost:5000/event_ArtP"
    headers = {"Content-Type": "application/json"}
    payload = {"ArtP": ArtP, "ArtC": ArtC, "FCD1": FCD1, "FCD2": FCD2}

    try:
        response = requests.post(url, json=payload, headers=headers)
        return mgp.Record()
    except Exception as e:
        return mgp.Record()

@mgp.read_proc
def send_http_request_CLM(CLM: str, ArtC: str, FCD1: str, FCD2: str) -> mgp.Record():
    """Sends an HTTP request when an EiffelFlowContextDefinedEvent is created."""
    url = "http://localhost:5000/event_CLM"
    headers = {"Content-Type": "application/json"}
    payload = {"CLM": CLM, "ArtC": ArtC, "FCD1": FCD1, "FCD2": FCD2}

    try:
        response = requests.post(url, json=payload, headers=headers)
        return mgp.Record()
    except Exception as e:
        return mgp.Record()
    
@mgp.read_proc
def send_http_request_impossible(CLM: str, ArtP: str, ArtC: str, FCD1: str, FCD2: str) -> mgp.Record():
    """Sends an HTTP request when an EiffelFlowContextDefinedEvent is created."""
    url = "http://localhost:5000/event_impossible"
    headers = {"Content-Type": "application/json"}
    payload = {"CLM": CLM, "ArtP": ArtP, "ArtC": ArtC, "FCD1": FCD1, "FCD2": FCD2}

    try:
        response = requests.post(url, json=payload, headers=headers)
        return mgp.Record()
    except Exception as e:
        return mgp.Record()
    
