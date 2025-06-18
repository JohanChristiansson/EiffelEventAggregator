############################################
#                                          #
#    Flask Server to get requests from     #
#         Neo4j Database triggers          # 
#                                          #
############################################




from flask import Flask, request, jsonify
import json
import logging
log = logging.getLogger('werkzeug')
#log.setLevel(logging.ERROR)

PRINT = False
LOG = True

app = Flask(__name__)

ARTIFACT_CREATED_COUNTER = 0
ARTIFACT_PUBLISHED_COUNTER = 0
CLM_COUNTER = 0
IMPOSSIBLE_COUNTER = 0
TEST_CASE_STARTED_COUNTER = 0
TEST_CASE_FINISHED_COUNTER = 0
TEST_SUITE_FINISHED_COUNTER = 0

@app.route('/trigger', methods=['POST'])
def triggers():
    return "yes", 200

@app.route('/event_ArtC', methods=['POST'])
def event_ArtC():
    """
    :use system;
    CALL apoc.trigger.install(
    'neo4j',
    'send_http_request',
    'WITH [n IN $createdNodes WHERE n.type = "EiffelArtifactCreatedEvent"] AS nodes
    UNWIND nodes AS n
    MATCH (n)-[:FLOW_CONTEXT]->(e:Event {type:"EiffelFlowContextDefinedEvent"})
    CALL apoc.load.jsonParams(                                                                                                                         
        "http://localhost:5000/event_ArtC",                                                                                                                 
        {`Content-Type`: "application/json"},                                                                                                          
        apoc.convert.toJson({ArtC: n.id, FCD: e.id})     
    ) YIELD value
    RETURN NULL',
    {phase:"afterAsync"}
    );
    """
    global ARTIFACT_CREATED_COUNTER, PRINT, LOG
    data = request.json  

    event_id = data.get("ArtC")
    context_id = data.get("FCD")

    ARTIFACT_CREATED_COUNTER += 1

    if context_id != "NONE" and event_id != "NONE":
        if LOG:
            with open("event_log.txt", "a") as f:
                f.write(f"{event_id},{context_id}\n")
        if PRINT:
            print(f"\033[32mALERT: ArtifactCreatedEvent {event_id} is linked to ContextDefinedEvent {context_id}\033[0m")
    #print(ARTIFACT_CREATED_COUNTER)


    return jsonify({"status": "alert received"}), 200


@app.route('/event_ArtP', methods=['POST'])
def event_ArtP():
    """
    :use system;
    CALL apoc.trigger.install(
    'neo4j',
    'artifact_published_trigger',
    'WITH [n IN $createdNodes WHERE n.type = "EiffelArtifactPublishedEvent"] AS nodes
    UNWIND nodes AS n 
    MATCH (n)-[:FLOW_CONTEXT]->(e:Event {type:"EiffelFlowContextDefinedEvent"}) 
    MATCH (n)-[:ARTIFACT]->(c:Event {type:"EiffelArtifactCreatedEvent"})-[:FLOW_CONTEXT]->(f:Event {type:"EiffelFlowContextDefinedEvent"})
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
    global ARTIFACT_PUBLISHED_COUNTER, PRINT
    data = request.json


    ArtP_event_id = data.get("ArtP")
    ArtC_event_id = data.get("ArtC")
    context_id1 = data.get("FCD1")
    context_id2 = data.get("FCD2")

    ARTIFACT_PUBLISHED_COUNTER += 1

    if context_id1 != "NONE" and ArtP_event_id != "NONE" and ArtC_event_id != "NONE" and context_id2 != "NONE":
        if PRINT:
            print(f"\033[31mALERT: ArtifactPublishedEvent {ArtP_event_id} is linked to ContextDefinedEvent {context_id1} and ArtifactCreatedEvent {ArtC_event_id}, which links to ContextDefinedEvent {context_id2}\033[0m")

    #print(f"Total ArtifactPublishedEvents processed: {ARTIFACT_PUBLISHED_COUNTER}")
    return jsonify({"status": "alert received"}), 200


@app.route('/event_CLM', methods=['POST'])
def event_CLM():
    """
    :use system;
    CALL apoc.trigger.install(
    'neo4j',
    'CLM_trigger',
    '
    WITH [n IN $createdNodes WHERE n.type = "EiffelConfidenceLevelModifiedEvent"] AS nodes
    UNWIND nodes AS n 
    MATCH (n)-[:FLOW_CONTEXT]->(e:Event {type:"EiffelFlowContextDefinedEvent"}) 
    MATCH (n)-[:SUBJECT]->(c:Event {type:"EiffelArtifactCreatedEvent"})-[:FLOW_CONTEXT]->(f:Event {type:"EiffelFlowContextDefinedEvent"})
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
    global CLM_COUNTER, PRINT
    data = request.json

    CLM_event_id = data.get("CLM")
    ArtC_event_id = data.get("ArtC")
    context_id1 = data.get("FCD1")
    context_id2 = data.get("FCD2")
    CLM_COUNTER = CLM_COUNTER + 1
    if context_id1 != "NONE" and CLM_event_id != "NONE" and ArtC_event_id != "NONE" and context_id2 != "NONE":
        if PRINT:
            print(f"\033[33mALERT: ConfidenceLevelModifiedEvent {CLM_event_id} is linked to ContextDefinedEvent {context_id1} and ArtifactCreatedEvent {ArtC_event_id}, which links to ContextDefinedEvent {context_id2}\033[0m")
    #print(CLM_COUNTER)
    return jsonify({"status": "alert received"}), 200


@app.route('/event_impossible', methods=['POST'])
def event_impossible():
    """
    :use system;
    CALL apoc.trigger.install(
        'neo4j',
        'impossible_trigger',
        '
        WITH [n IN $createdNodes WHERE n.type IN ["EiffelConfidenceLevelModifiedEvent", "EiffelArtifactPublishedEvent"]] AS nodes
        UNWIND nodes AS n 
        CALL apoc.do.case(
            [
                n.type = "EiffelConfidenceLevelModifiedEvent", 
                "MATCH (n)-[:FLOW_CONTEXT]->(e:Event {type:\\\"EiffelFlowContextDefinedEvent\\\"}) 
                MATCH (n)-[:SUBJECT]->(c:Event {type:\\\"EiffelArtifactCreatedEvent\\\"})-[:FLOW_CONTEXT]->(f:Event {type:\\\"EiffelFlowContextDefinedEvent\\\"})
                MATCH (c)<-[:ARTIFACT]-(d:Event {type:\\\"EiffelArtifactPublishedEvent\\\"})-[:FLOW_CONTEXT]->(g:Event {type:\\\"EiffelFlowContextDefinedEvent\\\"})
                WHERE e <> f AND e <> g AND f <> g
                CALL apoc.load.jsonParams(
                    \\\"http://localhost:5000/event_impossible\\\", 
                    {`Content-Type`: \\\"application/json\\\"},
                    apoc.convert.toJson({CLM: n.id, ArtP: d.id, ArtC: c.id, FCD1: e.id, FCD2: f.id, FCD3: g.id})  
                ) YIELD value
                RETURN NULL",

                n.type = "EiffelArtifactPublishedEvent", 
                "MATCH (n)-[:FLOW_CONTEXT]->(e:Event {type:\\\"EiffelFlowContextDefinedEvent\\\"}) 
                MATCH (n)-[:ARTIFACT]->(c:Event {type:\\\"EiffelArtifactCreatedEvent\\\"})-[:FLOW_CONTEXT]->(f:Event {type:\\\"EiffelFlowContextDefinedEvent\\\"})
                MATCH (c)<-[:SUBJECT]-(d:Event {type:\\\"EiffelConfidenceLevelModifiedEvent\\\"})-[:FLOW_CONTEXT]->(g:Event {type:\\\"EiffelFlowContextDefinedEvent\\\"})
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
    global IMPOSSIBLE_COUNTER, PRINT
    data = request.json

    CLM_event_id = data.get("CLM")
    ArtP_event_id = data.get("ArtP")
    ArtC_event_id = data.get("ArtC")
    context_id1 = data.get("FCD1")
    context_id2 = data.get("FCD2")
    context_id3 = data.get("FCD3")


    IMPOSSIBLE_COUNTER = IMPOSSIBLE_COUNTER+ 1
    if context_id1 != "NONE" and CLM_event_id != "NONE" and ArtP_event_id != "NONE" and ArtC_event_id != "NONE" and context_id2 != "NONE" and context_id3 != "NONE":
        if PRINT:
            print(f"\033[35mALERT: ConfidenceLevelModifiedEvent {CLM_event_id} is linked to ContextDefinedEvent {context_id1} and ArtifactCreatedEvent {ArtC_event_id}, which links to ContextDefinedEvent {context_id2}. ArtifactPublishedEvent {ArtP_event_id} also links to same ArtC as well as ContextDefinedEvent {context_id3}\033[0m")
    #print(IMPOSSIBLE_COUNTER)
    return jsonify({"status": "alert received"}), 200


@app.route('/event_TestCaseStarted', methods=['POST'])
def event_test_case_started():
    """
    :use system;
    CALL apoc.trigger.install(
        'neo4j',
        'test_case_started_aggregation',
        'WITH [n IN $createdNodes WHERE n.type = "EiffelTestCaseStartedEvent"] AS nodes
        UNWIND nodes AS n
        MATCH (n)-[:TEST_CASE_EXECUTION]->(t:Event {type: "EiffelTestCaseTriggeredEvent"})
        MATCH (t)-[:CONTEXT]->(s:Event {type: "EiffelTestSuiteStartedEvent"})
        CALL apoc.load.jsonParams(                                                                                                                          
            "http://localhost:5000/TestCaseStarted",
            {`Content-Type`: "application/json"},
            apoc.convert.toJson({TCS: n.id, TCT: t.id, Suite: s.id})     
        ) YIELD value
        RETURN NULL',
        {phase: "afterAsync"}
    );
    """
    global TEST_CASE_STARTED_COUNTER, PRINT
    data = request.json

    # Extract relevant fields
    TCS = data.get("TCS")
    TCT = data.get("TCT")
    Suite = data.get("Suite")

    TEST_CASE_STARTED_COUNTER += 1

    if PRINT and TCS and TCT and Suite:
        print(f"\033[32mALERT: TestCaseStarted {TCS} (Triggered: {TCT}, Suite: {Suite})\033[0m")

    return jsonify({"status": "TestCaseStarted event received"}), 200


@app.route('/event_TestCaseFinished', methods=['POST'])
def event_test_case_finished():
    """
    :use system;
    CALL apoc.trigger.install(
        'neo4j',
        'test_case_finished_aggregation',
        'WITH [n IN $createdNodes WHERE n.type = "EiffelTestCaseFinishedEvent"] AS nodes
        UNWIND nodes AS n
        MATCH (n)-[:TEST_CASE_EXECUTION]->(t:Event {type: "EiffelTestCaseTriggeredEvent"})
        MATCH (t)-[:CONTEXT]->(s:Event {type: "EiffelTestSuiteStartedEvent"})
        CALL apoc.load.jsonParams(                                                                                                                          
            "http://localhost:5000/TestCaseFinished",
            {`Content-Type`: "application/json"},
            apoc.convert.toJson({TCF: n.id, TCT: t.id, Suite: s.id})     
        ) YIELD value
        RETURN NULL',
        {phase: "afterAsync"}
    );
    """
    global TEST_CASE_FINISHED_COUNTER, PRINT
    data = request.json

    # Extract relevant fields
    TCF = data.get("TCF")
    TCT = data.get("TCT")
    Suite = data.get("Suite")

    TEST_CASE_FINISHED_COUNTER += 1

    if PRINT and TCF and TCT and Suite:
        print(f"\033[31mALERT: TestCaseFinished {TCF} (Triggered: {TCT}, Suite: {Suite})\033[0m")

    return jsonify({"status": "TestCaseFinished event received"}), 200


@app.route('/event_TestSuiteFinished', methods=['POST'])
def event_test_suite_finished():
    """
    :use system;
    CALL apoc.trigger.install(
        'neo4j',
        'test_suite_finished_aggregation',
        'WITH [n IN $createdNodes WHERE n.type = "EiffelTestSuiteFinishedEvent"] AS nodes
        UNWIND nodes AS n
        MATCH (n)-[:TEST_SUITE_EXECUTION]->(t:Event {type: "EiffelTestSuiteStartedEvent"})
        OPTIONAL MATCH (t)<-[:CONTEXT]-(a:Event {type: "EiffelTestCaseTriggeredEvent"})
        OPTIONAL MATCH (a)<-[:TEST_CASE_EXECUTION]-(b:Event)
        WITH n.id AS TSF, t.id AS TSS, COLLECT(a) AS TestCases, COLLECT(b) AS TestExecutions
        CALL apoc.load.jsonParams(                                                                                                                          
            "http://localhost:5000/TestSuiteFinished",
            {`Content-Type`: "application/json"},
            apoc.convert.toJson({TestCases: TestCases, TestExecutions: TestExecutions, TSF: TSF, TSS: TSS})     
        ) YIELD value
        RETURN NULL',
        {phase: "afterAsync"}
    );
    """
    global TEST_SUITE_FINISHED_COUNTER, PRINT
    data = request.json

    # Extract relevant fields
    TSF = data.get("TSF")
    TSS = data.get("TSS")
    TestCases = data.get("TestCases", [])
    TestExecutions = data.get("TestExecutions", [])

    TEST_SUITE_FINISHED_COUNTER += 1

    if PRINT and TSF and TSS:
        print(f"\033[34mALERT: TestSuiteFinished {TSF} (Started: {TSS})\033[0m")
        print(f"\033[34m  - Test Cases: {len(TestCases)}\033[0m")
        print(f"\033[34m  - Test Executions: {len(TestExecutions)}\033[0m")

    return jsonify({"status": "TestSuiteFinished event received"}), 200

global_artC_fcd_counter_if_statement = 0


global_artC_fcd_counter = 0
@app.route('/test2', methods=['POST'])
def test2():
    data = request.get_json()
    json_str = data['parameter'][0]['value']
    data = json.loads(json_str)
    with open("event_log.txt", "a") as f:
        f.write(f"{data['id']}\n")

    return "ok", 200


subscriptions = 0
@app.route('/eiffel/specific_id', methods=['POST'])
def specific_id():
   # subscriptions += 1
    print("subscriptions triggered", request.get_json())
    return "ok", 200


if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True, port=5000, threaded=True)
