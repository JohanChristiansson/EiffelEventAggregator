#Check graph for cycles
import sys

def is_cyclic(graph, event_id, visited, rec_stack):
    """Detects if there is a cycle in the graph using DFS."""

    if visited[event_id] == False:
        visited[event_id] = True
        rec_stack[event_id] = True
        
        for neighbor in graph.get(event_id, []):
            print(event_id)
            if visited[neighbor] == False and is_cyclic(graph, neighbor, visited, rec_stack):
                return True
            elif rec_stack[neighbor] == True:
                return True

    rec_stack[event_id] = False
    return False

def check_for_cycles(created_events):
    print(len(created_events), "in verify gen")
    """Check the entire event graph for cycles."""
    visited = {event["meta"]["id"]: False for event in created_events}
    rec_stack = {event["meta"]["id"]: False for event in created_events}
    graph = {}

    for event in created_events:
        event_id = event["meta"]["id"]
        links = event["links"]
        graph[event_id] = [link["target"] for link in links]

    for event in created_events:
        event_id = event["meta"]["id"]
        if not visited[event_id]:
            if is_cyclic(graph, event_id, visited, rec_stack):
                print("Cycle detected!")
                return False

    print("No cycles detected. The graph is acyclic")
    return True

if __name__ == "__main__":
    # Test a cycle
    created_events = [
        {
            "meta": {"id": "1", "type": "EiffelContextDefinedEvent", "version": "1.0.0", "source": {"domainId": "example.domain"}},
            "data": {},
            "links": [{"target": "2", "type": "ELEMENT"}]
        },
        {
            "meta": {"id": "2", "type": "EiffelArtifactCreatedEvent", "version": "1.0.0", "source": {"domainId": "example.domain"}},
            "data": {},
            "links": [{"target": "3", "type": "ELEMENT"}]
        },
        {
            "meta": {"id": "3", "type": "EiffelArtifactPublishedEvent", "version": "1.0.0", "source": {"domainId": "example.domain"}},
            "data": {},
            "links": []
        },
        {
            "meta": {"id": "4", "type": "EiffelConfidenceLevelModified", "version": "1.0.0", "source": {"domainId": "example.domain"}},
            "data": {},
            "links": [{"target": "5", "type": "ELEMENT"}]
        },
        {
            "meta": {"id": "5", "type": "EiffelConfidenceLevelModified", "version": "1.0.0", "source": {"domainId": "example.domain"}},
            "data": {},
            "links": [{"target": "4", "type": "ELEMENT"}]
        }
    ]
    
    check_for_cycles(created_events)

