#############################################################################################################################################################
#                                                                                                                                                           #
#                                                 Flask Server to get requests from Neo4j Database triggers                                                 #
#                                                                Uses following Cypher code                                                                 #
#                                                                                                                                                           #
#    :use system;                                                                                                                                           #
#    CALL apoc.trigger.install(                                                                                                                             # 
#        'neo4j',                                                                                                                                           #
#        'send_http_request',                                                                                                                               #
#        'CALL apoc.util.sleep(50)                                                                                                                          #
#        UNWIND $createdNodes AS n                                                                                                                          #
#        MATCH (n {type:"EiffelArtifactCreatedEvent"})-[:CONTEXT_DEFINED]->(e:Event {type:"EiffelContextDefinedEvent"})                                     #
#        CALL apoc.load.jsonParams(                                                                                                                         #
#            "http://localhost:5000/event",                                                                                                                 #
#            {`Content-Type`: "application/json"},                                                                                                          #
#            apoc.convert.toJson({ArtC: n.id, FCD: e.id})                                                                                                   #
#        ) YIELD value                                                                                                                                      #
#        RETURN NULL',                                                                                                                                      #
#        {phase:"afterAsync"}                                                                                                                               #
#    );                                                                                                                                                     #
#                                                                                                                                                           #
#############################################################################################################################################################




from flask import Flask, request, jsonify

app = Flask(__name__)
AAA = 0
@app.route('/event', methods=['POST'])
def event():
    global AAA
    data = request.json

    event_id = data.get("ArtC")
    context_id = data.get("FCD")
    AAA = AAA + 1
    if context_id != "NONE" and event_id != "NONE":
        print(f"ALERT: ArtifactCreatedEvent {event_id} is linked to ContextDefinedEvent {context_id}")
    print(AAA)
    return jsonify({"status": "alert received"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
    

