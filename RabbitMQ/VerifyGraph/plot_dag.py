import matplotlib.pyplot as plt
import networkx as nx

def plot_graph_from_events(created_events):
    """Plot the graph using event data from created events."""
    
    G = nx.DiGraph()

    for event in created_events:
        event_id = event["meta"]["id"] 
        links = event["links"] 
        G.add_node(event_id)
        for link in links:
            target_event_id = link["target"] 
            G.add_edge(event_id, target_event_id)  

    pos = nx.spring_layout(G, k=0.5, scale=2, iterations=50)
    plt.figure(figsize=(15, 15)) 

    nx.draw(G, pos, with_labels=True, node_size=700, node_color="skyblue", font_size=10, font_weight="bold", alpha=0.7, edge_color="gray")

    plt.title("Eiffel Event Graph")
    plt.axis("off") 
    

    plt.xlim(-2, 2)
    plt.ylim(-2, 2)

    #Save it as a png
    plt.savefig("graph_plot.png", format = "png")

if __name__ == "__main__":
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
            "links": [{"target": "1", "type": "ELEMENT"}]
        },
        {
            "meta": {"id": "4", "type": "EiffelConfidenceLevelModified", "version": "1.0.0", "source": {"domainId": "example.domain"}},
            "data": {},
            "links": []
        }
    ]
    
    plot_graph_from_events(created_events)  # Call the plot function with event data
