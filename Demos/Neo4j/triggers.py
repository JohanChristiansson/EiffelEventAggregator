from neo4j import GraphDatabase
import time

NEO4J_URI = "bolt://localhost:7690"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "demodemo"

class EiffelTriggerMonitor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def check_new_artifact_events(self):
        """Detects new EiffelArtifactCreatedEvents with CONTEXT_DEFINED links."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Event { type: "EiffelArtifactCreatedEvent"})-[:CONTEXT_DEFINED]->(c:Event {type: "EiffelContextDefinedEvent"})
                WHERE e.checked IS NULL
                SET e.checked = true
                RETURN e.id AS artifact_id, c.id AS context_id
            """)
            for record in result:
                print(f"🔔  ✅ ARTIFACT CREATED: ArtifactCreatedEvent {record['artifact_id']} is linked to ContextDefinedEvent {record['context_id']}")
            
            result2 = session.run("""
                MATCH (d:Event {type: "EiffelContextDefinedEvent"})<-[:CONTEXT_DEFINED]-(a:Event {type: "EiffelArtifactCreatedEvent"})<-[:ARTIFACT]-(e:Event { type: "EiffelArtifactPublishedEvent"})-[:CONTEXT_DEFINED]->(c:Event {type: "EiffelContextDefinedEvent"})
                WHERE e.checked IS NULL AND d <> c
                SET e.checked = true
                RETURN a.id AS artifactC_id, e.id AS artifactP_id, d.id AS contextC_id, c.id AS contextP_id
            """)
            for record in result2:
                print(f"🔔  ✅🎈 ARTIFACT PUBLISHED: ArtifactPublishedEvent: {record['artifactP_id']}, ArtifactCreatedEvent: {record['artifactC_id']}, ContextDefinedEvent with ArtC: {record['contextC_id']}, ContextDefinedEvent with ArtP: {record['contextP_id']}")

            result3 = session.run("""
                MATCH (d:Event {type: "EiffelContextDefinedEvent"})<-[:CONTEXT_DEFINED]-(a:Event {type: "EiffelArtifactCreatedEvent"})<-[:SUBJECT]-(e:Event { type: "EiffelConfidenceLevelModified"})-[:CONTEXT_DEFINED]->(c:Event {type: "EiffelContextDefinedEvent"})
                WHERE e.checked IS NULL AND d <> c
                SET e.checked = true
                RETURN a.id AS artifactC_id, e.id AS CLM_id, d.id AS contextC_id, c.id AS contextCLM_id
            """)
            for record in result3:
                print(f"🔔  ✅💛 CONFIDENCE LEVEL MODIFIED: ConfidenceLevelModified: {record['CLM_id']}, ArtifactCreatedEvent: {record['artifactC_id']}, ContextDefinedEvent with ArtC: {record['contextC_id']}, ContextDefinedEvent with CLM: {record['contextCLM_id']}")

            result4 = session.run("""
                MATCH (d:Event {type: "EiffelContextDefinedEvent"})<-[:CONTEXT_DEFINED]-(a:Event {type: "EiffelArtifactCreatedEvent"})<-[:SUBJECT]-(e:Event { type: "EiffelConfidenceLevelModified"})-[:CONTEXT_DEFINED]->(c:Event {type: "EiffelContextDefinedEvent"})
                MATCH (a)<-[:ARTIFACT]-(e2:Event {type:"EiffelArtifactPublishedEvent"})-[:CONTEXT_DEFINED]->(c2:Event {type: "EiffelContextDefinedEvent"})
                WHERE e.checked1 IS NULL OR e2.checked1 IS NULL AND d <> c AND c <> c2 AND d <> c2
                SET e.checked1 = true
                SET e2.checked1 = true
                RETURN a.id AS artifactC_id, e.id AS CLM_id, d.id AS contextC_id, c.id AS contextCLM_id, e2.id AS artifactP_id, c2 AS contextP_id
            """)
            for record in result4:
                print(f"🔔  ✅🎈💛 IMPOSSIBLE FOUND: ConfidenceLevelModified: {record['CLM_id']}, ArtifactPublishedEvent: {record['artifactP_id']}, ArtifactCreatedEvent: {record['artifactC_id']}, ContextDefinedEvent with ArtC: {record['contextC_id']}, ContextDefinedEvent with CLM: {record['contextCLM_id']}, ContextDefinedEvent with ArtP: {record['contextP_id']}")

    def run(self):
        """Continuously checks for new events every 5 seconds."""
        try:
            while True:
                self.check_new_artifact_events()
                time.sleep(0.2)  # Check every 0.5 seconds
        except KeyboardInterrupt:
            print("🛑 Stopping Eiffel Trigger Monitor.")
            self.close()

# Start the monitoring script
monitor = EiffelTriggerMonitor(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
monitor.run()