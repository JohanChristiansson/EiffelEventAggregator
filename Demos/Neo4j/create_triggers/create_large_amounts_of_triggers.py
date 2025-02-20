import random

event_types = [
    "EiffelActivityTriggeredEvent",
    "EiffelActivityCanceledEvent",
    "EiffelActivityStartedEvent",
    "EiffelActivityFinishedEvent",
    "EiffelArtifactCreatedEvent",
    "EiffelArtifactDeployedEvent",
    "EiffelArtifactPublishedEvent",
    "EiffelArtifactReusedEvent",
    "EiffelConfidenceLevelModifiedEvent",
    "EiffelEnvironmentDefinedEvent",
    "EiffelCompositionDefinedEvent",
    "EiffelSourceChangeCreatedEvent",
    "EiffelSourceChangeSubmittedEvent",
    "EiffelFlowContextDefinedEvent",
    "EiffelTestCaseTriggeredEvent",
    "EiffelTestCaseCanceledEvent",
    "EiffelTestCaseStartedEvent",
    "EiffelTestCaseFinishedEvent",
    "EiffelTestSuiteStartedEvent",
    "EiffelTestSuiteFinishedEvent",
    "EiffelIssueVerifiedEvent",
    "EiffelTestExecutionRecipeCollectionCreatedEvent",
    "EiffelAnnouncementPublishedEvent",
    "EiffelIssueDefinedEvent"
]

link_types = [
    "ACTIVITY_EXECUTION",
    "ORIGINAL_TRIGGER",
    "PRECURSOR",
    "MODIFIED_ANNOUNCEMENT",
    "COMPOSITION",
    "ENVIRONMENT",
    "PREVIOUS_VERSION",
    "CONTEXT",
    "CAUSE",
    "ARTIFACT",
    "CONFIGURATION",
    "FLOW_CONTEXT",
    "REUSED_ARTIFACT",
    "ELEMENT",
    "CONFIDENCE_BASIS",
    "SUB_CONFIDENCE_LEVEL",
    "RUNTIME_ENVIRONMENT",
    "FAILED_ISSUE",
    "INCONCLUSIVE_ISSUE",
    "IUT",
    "SUCCESSFUL_ISSUE",
    "VERIFICATION_BASIS",
    "BASE",
    "DERESOLVED_ISSUE",
    "PARTIALLY_RESOLVED_ISSUE",
    "RESOLVED_ISSUE",
    "CHANGE",
    "TEST_CASE_EXECUTION",
    "TERC"
]

def main(num_triggers = 1000):
    triggers = []
    for i in range(num_triggers):
        source_event = random.choice(event_types)
        target_event = random.choice(event_types)

        link_type = random.choice(link_types)
        
        trigger_name = f"trigger_{i+1}"
        url_endpoint = f"http://localhost:5000/triggers"
        
        #Build the APOC trigger installation query string
        cypher_query = f"""
            CALL apoc.trigger.install(
            'neo4j',
            '{trigger_name}',
            'WITH [n IN $createdNodes WHERE n.type = "{source_event}"] AS nodes
            UNWIND nodes AS n
            MATCH (n)-[:{link_type}]->(e:Event {{type:"{target_event}"}})
            CALL apoc.load.jsonParams(
                "{url_endpoint}",
                {{`Content-Type`: "application/json"}},
                apoc.convert.toJson({{source: n.id, target: e.id}})
            ) YIELD value
            RETURN NULL',
            {{phase:"afterAsync"}}
            );"""
        
        triggers.append(cypher_query)
    with open("apoc_triggers.txt", "w") as f:
        for trigger in triggers:
            f.write(trigger)
       ## print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()
