from artifact_created_ids import artifact_created_ids

# Sort IDs to ensure deterministic ordering
artifact_created_ids.sort()

artifact_created_ids = artifact_created_ids[:100]
print(len(artifact_created_ids))
# Create a Cypher list literal for filtering the nodes by ID
artifact_ids_list_literal = "[" + ", ".join(f'"{artifact_id}"' for artifact_id in artifact_created_ids) + "]"

# Build the CASE statement mapping each artifact id to its endpoint.
# In this example, each endpoint is constructed as "http://localhost:5000/trigger_X",
# where X is the 1-based index of the artifact id.
mapping_lines = []
for i, artifact_id in enumerate(artifact_created_ids):
    endpoint = f"http://localhost:5000/trigger"
    # endpoint = f"http://localhost:5000/trigger_{i+1}"
    mapping_lines.append(f'WHEN "{artifact_id}" THEN "{endpoint}"')
    
# Combine into a single CASE statement.  
# The CASE returns the corresponding endpoint for n.id, or null if not found.
case_statement = "CASE n.id " + "\n    ".join(mapping_lines) + " ELSE null END"

# Build the combined APOC trigger installation query.
cypher_query = f""":use system;
CALL apoc.trigger.install(
  'neo4j',
  'combined_artifact_trigger',
  'WITH [n IN $createdNodes WHERE n.type = "EiffelArtifactCreatedEvent" AND n.id IN {artifact_ids_list_literal}] AS nodes
  UNWIND nodes AS n
  MATCH (n)-[:FLOW_CONTEXT]->(e:Event {{type:"EiffelFlowContextDefinedEvent"}})
  WITH n, e, {case_statement} AS endpoint
  WHERE endpoint IS NOT NULL
  CALL apoc.load.jsonParams(
    endpoint,
    {{`Content-Type`: "application/json"}},
    apoc.convert.toJson({{ArtC: n.id, FCD: e.id}})
  ) YIELD value
  RETURN NULL',
  {{phase:"afterAsync"}}
);
"""

# Write the combined trigger query to a file
with open("combined_artifact_trigger.txt", "w") as f:
    f.write(cypher_query)

print("Combined artifact trigger written to combined_artifact_trigger.txt")
