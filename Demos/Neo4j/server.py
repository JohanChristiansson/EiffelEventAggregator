############################################
#                                          #
#    Flask Server to get requests from     #
#         Neo4j Database triggers          # 
#                                          #
############################################




from flask import Flask, request, jsonify

app = Flask(__name__)
ARTIFACT_CREATED_COUNTER = 0
@app.route('/event_ArtC', methods=['POST'])
def event_ArtC():
    """
    :use system;                                                                                                                                           
    CALL apoc.trigger.install(                                                                                                                              
        'neo4j',                                                                                                                                           
        'send_http_request',                                                                                                                               
        'CALL apoc.util.sleep(50)                                                                                                                          
        UNWIND $createdNodes AS n                                                                                                                          
        MATCH (n {type:"EiffelArtifactCreatedEvent"})-[:CONTEXT_DEFINED]->(e:Event {type:"EiffelContextDefinedEvent"})                                     
        CALL apoc.load.jsonParams(                                                                                                                         
            "http://localhost:5000/event",                                                                                                                 
            {`Content-Type`: "application/json"},                                                                                                          
            apoc.convert.toJson({ArtC: n.id, FCD: e.id})                                                                                                   
        ) YIELD value                                                                                                                                      
        RETURN NULL',                                                                                                                                      
        {phase:"afterAsync"}                                                                                                                               
    );  
    """
    global ARTIFACT_CREATED_COUNTER
    data = request.json

    event_id = data.get("ArtC")
    context_id = data.get("FCD")
    ARTIFACT_CREATED_COUNTER = ARTIFACT_CREATED_COUNTER + 1
    if context_id != "NONE" and event_id != "NONE":
        print(f"\033[32mALERT: ArtifactCreatedEvent {event_id} is linked to ContextDefinedEvent {context_id}\033[0m")
    print(ARTIFACT_CREATED_COUNTER)
    return jsonify({"status": "alert received"}), 200

ARTIFACT_PUBLISHED_COUNTER = 0
@app.route('/event_ArtP', methods=['POST'])
def event_ArtP():
    """
    :use system;
    CALL apoc.trigger.install(
        'neo4j',
        'artifact_published_trigger',
        'CALL apoc.util.sleep(50)
        UNWIND $createdNodes AS n 
        MATCH (n {type:"EiffelArtifactPublishedEvent"})
        MATCH (n)-[:CONTEXT_DEFINED]->(e:Event {type:"EiffelContextDefinedEvent"}) 
        MATCH (n)-[:ARTIFACT]->(c:Event {type:"EiffelArtifactCreatedEvent"})-[CONTEXT_DEFINED]->(f:Event {type:"EiffelContextDefinedEvent"})
        WHERE e <> f
        CALL apoc.load.jsonParams(
            "http://localhost:5000/event_ArtP", 
            {`Content-Type`: "application/json"},
            apoc.convert.toJson({ArtP: n.id, ArtC: c.id, FCD1: e.id, FCD2: f.id})  
        ) YIELD value
        RETURN NULL', 
        {phase:"afterAsync"}
    );
    """
    global ARTIFACT_PUBLISHED_COUNTER
    data = request.json

    ArtP_event_id = data.get("ArtP")
    ArtC_event_id = data.get("ArtC")
    context_id1 = data.get("FCD1")
    context_id2 = data.get("FCD2")
    ARTIFACT_PUBLISHED_COUNTER = ARTIFACT_PUBLISHED_COUNTER + 1
    if context_id1 != "NONE" and ArtP_event_id != "NONE" and ArtC_event_id != "NONE" and context_id2 != "NONE":
        print(f"\033[31mALERT: ArtifactPublishedEvent {ArtP_event_id} is linked to ContextDefinedEvent {context_id1} and ArtifactCreatedEvent {ArtC_event_id}, which links to ContextDefinedEvent {context_id2}\033[0m")
    print(ARTIFACT_PUBLISHED_COUNTER)
    return jsonify({"status": "alert received"}), 200

CLM_COUNTER = 0
@app.route('/event_CLM', methods=['POST'])
def event_CLM():
    """
    :use system;
    CALL apoc.trigger.install(
        'neo4j',
        'CLM_trigger',
        'CALL apoc.util.sleep(50)
        UNWIND $createdNodes AS n 
        MATCH (n {type:"EiffelConfidenceLevelModified"})
        MATCH (n)-[:CONTEXT_DEFINED]->(e:Event {type:"EiffelContextDefinedEvent"}) 
        MATCH (n)-[:SUBJECT]->(c:Event {type:"EiffelArtifactCreatedEvent"})-[CONTEXT_DEFINED]->(f:Event {type:"EiffelContextDefinedEvent"})
        WHERE e <> f
        CALL apoc.load.jsonParams(
            "http://localhost:5000/event_CLM", 
            {`Content-Type`: "application/json"},
            apoc.convert.toJson({CLM: n.id, ArtC: c.id, FCD1: e.id, FCD2: f.id})  
        ) YIELD value
        RETURN NULL', 
        {phase:"afterAsync"}
    );
    """
    global CLM_COUNTER
    data = request.json

    CLM_event_id = data.get("CLM")
    ArtC_event_id = data.get("ArtC")
    context_id1 = data.get("FCD1")
    context_id2 = data.get("FCD2")
    CLM_COUNTER = CLM_COUNTER + 1
    if context_id1 != "NONE" and CLM_event_id != "NONE" and ArtC_event_id != "NONE" and context_id2 != "NONE":
        print(f"\033[33mALERT: ConfidenceLevelModified {CLM_event_id} is linked to ContextDefinedEvent {context_id1} and ArtifactCreatedEvent {ArtC_event_id}, which links to ContextDefinedEvent {context_id2}\033[0m")
    print(CLM_COUNTER)
    return jsonify({"status": "alert received"}), 200

IMPOSSIBLE_COUNTER = 0
@app.route('/event_impossible', methods=['POST'])
def event_impossible():
    """
    :use system;
    CALL apoc.trigger.install(
        'neo4j',
        'impossible_trigger',
        '
        CALL apoc.util.sleep(50)
        UNWIND $createdNodes AS n 
        CALL apoc.do.case(
            [
                n.type = "EiffelConfidenceLevelModified", 
                "MATCH (n:Event)-[:CONTEXT_DEFINED]->(e:Event {type:\\\"EiffelContextDefinedEvent\\\"}) 
                MATCH (n)-[:SUBJECT]->(c:Event {type:\\\"EiffelArtifactCreatedEvent\\\"})-[:CONTEXT_DEFINED]->(f:Event {type:\\\"EiffelContextDefinedEvent\\\"})
                MATCH (c)<-[:ARTIFACT]-(d:Event {type:\\\"EiffelArtifactPublishedEvent\\\"})-[:CONTEXT_DEFINED]->(g:Event {type:\\\"EiffelContextDefinedEvent\\\"})
                WHERE e <> f AND e <> g AND f <> g
                CALL apoc.load.jsonParams(
                    \\\"http://localhost:5000/event_impossible\\\", 
                    {`Content-Type`: \\\"application/json\\\"},
                    apoc.convert.toJson({CLM: n.id, ArtP: d.id, ArtC: c.id, FCD1: e.id, FCD2: f.id, FCD3: g.id})  
                ) YIELD value
                RETURN NULL",

                n.type = "EiffelArtifactPublishedEvent", 
                "MATCH (n:Event)-[:CONTEXT_DEFINED]->(e:Event {type:\\\"EiffelContextDefinedEvent\\\"}) 
                MATCH (n)-[:ARTIFACT]->(c:Event {type:\\\"EiffelArtifactCreatedEvent\\\"})-[:CONTEXT_DEFINED]->(f:Event {type:\\\"EiffelContextDefinedEvent\\\"})
                MATCH (c)<-[:SUBJECT]-(d:Event {type:\\\"EiffelConfidenceLevelModified\\\"})-[:CONTEXT_DEFINED]->(g:Event {type:\\\"EiffelContextDefinedEvent\\\"})
                WHERE e <> f AND e <> g AND f <> g
                CALL apoc.load.jsonParams(
                    \\\"http://localhost:5000/event_impossible\\\", 
                    {`Content-Type`: \\\"application/json\\\"},
                    apoc.convert.toJson({CLM: d.id, ArtP: n.id, ArtC: c.id, FCD1: g.id, FCD2: f.id, FCD3: e.id})  
                ) YIELD value
                RETURN NULL"
            ],
            "RETURN NULL",
            {n: n}
        ) YIELD value
        RETURN NULL', 
        {phase:"afterAsync"}
    );
    """
    global IMPOSSIBLE_COUNTER
    data = request.json

    CLM_event_id = data.get("CLM")
    ArtP_event_id = data.get("ArtP")
    ArtC_event_id = data.get("ArtC")
    context_id1 = data.get("FCD1")
    context_id2 = data.get("FCD2")
    context_id3 = data.get("FCD3")


    IMPOSSIBLE_COUNTER = IMPOSSIBLE_COUNTER+ 1
    if context_id1 != "NONE" and CLM_event_id != "NONE" and ArtP_event_id != "NONE" and ArtC_event_id != "NONE" and context_id2 != "NONE" and context_id3 != "NONE":
        print(f"\033[35mALERT: ConfidenceLevelModified {CLM_event_id} is linked to ContextDefinedEvent {context_id1} and ArtifactCreatedEvent {ArtC_event_id}, which links to ContextDefinedEvent {context_id2}. ArtifactPublishedEvent {ArtP_event_id} also links to same ArtC as well as ContextDefinedEvent {context_id3}\033[0m")
    print(IMPOSSIBLE_COUNTER)
    return jsonify({"status": "alert received"}), 200



if __name__ == '__main__':
    app.run(debug=True, port=5000)
    

