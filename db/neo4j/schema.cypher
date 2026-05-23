// ----------------------------------------------------------------------------
// Open Harness Hub — Neo4j / Memgraph graph schema (v0.1.0)
//
// The catalog is naturally a graph:
//   harness  -- CONSUMES -->  knowledge-pack
//   pipeline -- STEP_OF -->   harness / tool / rule-pack / processor
//   benchmark-- USES -->      pipeline / dataset / rubric
//   harness  -- EMITS -->     knowledge-leaf-type
//
// This Cypher schema sets constraints + indexes and ingests one sample
// artifact. Use scripts/db/load_neo4j.py (TBA) for bulk import.
// ----------------------------------------------------------------------------

// Uniqueness constraints
CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS
  FOR (a:Artifact) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT rule_id_unique IF NOT EXISTS
  FOR (r:Rule) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT leaf_id_unique IF NOT EXISTS
  FOR (l:KnowledgeLeaf) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT industry_id_unique IF NOT EXISTS
  FOR (i:Industry) REQUIRE i.id IS UNIQUE;

CREATE CONSTRAINT capability_id_unique IF NOT EXISTS
  FOR (c:Capability) REQUIRE c.id IS UNIQUE;

// Lookup indexes
CREATE INDEX artifact_type IF NOT EXISTS
  FOR (a:Artifact) ON (a.type);

CREATE INDEX artifact_lifecycle IF NOT EXISTS
  FOR (a:Artifact) ON (a.lifecycle);

CREATE INDEX leaf_type IF NOT EXISTS
  FOR (l:KnowledgeLeaf) ON (l.leaf_type);

// Full-text index over name + description
CREATE FULLTEXT INDEX artifact_fts IF NOT EXISTS
  FOR (a:Artifact) ON EACH [a.name, a.description, a.tags];

// Vector index (Neo4j 5.18+ has native vector indexes)
CREATE VECTOR INDEX catalog_vec IF NOT EXISTS
  FOR (a:Artifact) ON a.embedding
  OPTIONS { indexConfig: { `vector.dimensions`: 384, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX knowledge_vec IF NOT EXISTS
  FOR (l:KnowledgeLeaf) ON l.embedding
  OPTIONS { indexConfig: { `vector.dimensions`: 384, `vector.similarity_function`: 'cosine' } };

// Relationship types used:
//   (:Artifact)-[:HAS_INDUSTRY]->(:Industry)
//   (:Artifact)-[:HAS_CAPABILITY]->(:Capability)
//   (:Artifact)-[:CONSUMES_LEAF_TYPE]->(:LeafType)
//   (:Artifact)-[:EMITS_LEAF_TYPE]->(:LeafType)
//   (:Artifact)-[:STEP_OF {position}]->(:Artifact)
//   (:Artifact)-[:USES {role}]->(:Artifact)
//   (:Artifact)-[:SUPERSEDED_BY]->(:Artifact)
//   (:KnowledgeLeaf)-[:IN_PACK]->(:Artifact)
//   (:Rule)-[:IN_PACK]->(:Artifact)
//   (:Rule)-[:HAS_CATEGORY]->(:Category)

// Sample ingest (one harness)
MERGE (h:Artifact {id: 'harness/text-safety-review'})
  ON CREATE SET h.type = 'harness',
                h.name = 'Text Safety Review',
                h.lifecycle = 'beta',
                h.trust_boundary = 'local';

MERGE (i:Industry {id: 'cross_industry'})
MERGE (h)-[:HAS_INDUSTRY]->(i);

// Useful queries:
//
//  // Find all pipelines that use a given harness
//  MATCH (p:Artifact)-[:STEP_OF]->(h:Artifact {id: 'harness/text-safety-review'})
//  WHERE p.type = 'pipeline'
//  RETURN p.id, p.name;
//
//  // Vector search: 10 nearest knowledge leaves to a query vector
//  CALL db.index.vector.queryNodes('knowledge_vec', 10, $query_vector)
//  YIELD node, score
//  RETURN node.id, node.leaf_type, score;
//
//  // 2-hop graph: from a pipeline, find all leaf types it consumes
//  MATCH (p:Artifact {id: 'pipeline/research-entity'})-[:STEP_OF]->(:Artifact)-[:CONSUMES_LEAF_TYPE]->(t:LeafType)
//  RETURN DISTINCT t.id;
