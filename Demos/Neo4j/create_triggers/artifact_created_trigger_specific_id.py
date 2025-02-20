from artifact_created_ids import artifact_created_ids

artifact_created_ids.sort()

output_file = "artifact_created_trigger_for_specific_id.txt"

# Open the file to write triggers
with open(output_file, "w") as f:
    for i, artifact_id in enumerate(artifact_created_ids):
        if i == 100:
            break
        trigger_name = f"trigger_artifact_{i+1}"
        cypher_query = f"""
            CALL apoc.trigger.install(
            'neo4j',
            '{trigger_name}',
            'WITH [n IN $createdNodes WHERE n.type = "EiffelArtifactCreatedEvent" AND n.id = "{artifact_id}"] AS nodes
            UNWIND nodes AS n
            MATCH (n)-[:FLOW_CONTEXT]->(e:Event {{type:"EiffelFlowContextDefinedEvent"}})
            CALL apoc.load.jsonParams(
                "http://localhost:5000/trigger/",
                {{`Content-Type`: "application/json"}},
                apoc.convert.toJson({{ArtC: n.id, FCD: e.id}})
            ) YIELD value
            RETURN NULL',
            {{phase:"afterAsync"}}
            );
        """
        # Write to file
        f.write(cypher_query)
        # f.write("\n" + "=" * 80 + "\n\n")


print(f"Generated {i} specific ID APOC triggers in {output_file}")
