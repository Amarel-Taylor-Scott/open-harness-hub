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
// component. Use scripts/db/load_neo4j.py (TBA) for bulk import.
// ----------------------------------------------------------------------------

// Uniqueness constraints
CREATE CONSTRAINT component_id_unique IF NOT EXISTS
  FOR (a:Component) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT rule_id_unique IF NOT EXISTS
  FOR (r:Rule) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT leaf_id_unique IF NOT EXISTS
  FOR (l:KnowledgeLeaf) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT industry_id_unique IF NOT EXISTS
  FOR (i:Industry) REQUIRE i.id IS UNIQUE;

CREATE CONSTRAINT capability_id_unique IF NOT EXISTS
  FOR (c:Capability) REQUIRE c.id IS UNIQUE;

// Lookup indexes
CREATE INDEX component_type IF NOT EXISTS
  FOR (a:Component) ON (a.type);

CREATE INDEX component_lifecycle IF NOT EXISTS
  FOR (a:Component) ON (a.lifecycle);

CREATE INDEX leaf_type IF NOT EXISTS
  FOR (l:KnowledgeLeaf) ON (l.leaf_type);

// Full-text index over name + description
CREATE FULLTEXT INDEX component_fts IF NOT EXISTS
  FOR (a:Component) ON EACH [a.name, a.description, a.tags];

// Vector index (Neo4j 5.18+ has native vector indexes).
// Dimension and similarity are canonical registry values exported by:
//   python3 -m scripts.db.vector_config_registry --format json
CREATE VECTOR INDEX catalog_vec IF NOT EXISTS
  FOR (a:Component) ON a.embedding
  OPTIONS { indexConfig: { `vector.dimensions`: 384, `vector.similarity_function`: 'cosine' } };

CREATE VECTOR INDEX knowledge_vec IF NOT EXISTS
  FOR (l:KnowledgeLeaf) ON l.embedding
  OPTIONS { indexConfig: { `vector.dimensions`: 384, `vector.similarity_function`: 'cosine' } };

// Relationship types used:
//   (:Component)-[:HAS_INDUSTRY]->(:Industry)
//   (:Component)-[:HAS_CAPABILITY]->(:Capability)
//   (:Component)-[:CONSUMES_LEAF_TYPE]->(:LeafType)
//   (:Component)-[:EMITS_LEAF_TYPE]->(:LeafType)
//   (:Component)-[:STEP_OF {position}]->(:Component)
//   (:Component)-[:USES {role}]->(:Component)
//   (:Component)-[:SUPERSEDED_BY]->(:Component)
//   (:KnowledgeLeaf)-[:IN_PACK]->(:Component)
//   (:Rule)-[:IN_PACK]->(:Component)
//   (:Rule)-[:HAS_CATEGORY]->(:Category)

// Sample ingest (one harness)
MERGE (h:Component {id: 'harness/text-safety-review'})
  ON CREATE SET h.type = 'harness',
                h.name = 'Text Safety Review',
                h.lifecycle = 'beta',
                h.trust_boundary = 'local';

MERGE (i:Industry {id: 'cross_industry'})
MERGE (h)-[:HAS_INDUSTRY]->(i);

// Useful queries:
//
//  // Find all pipelines that use a given harness
//  MATCH (p:Component)-[:STEP_OF]->(h:Component {id: 'harness/text-safety-review'})
//  WHERE p.type = 'pipeline'
//  RETURN p.id, p.name;
//
//  // Vector search: 10 nearest knowledge leaves to a query vector
//  CALL db.index.vector.queryNodes('knowledge_vec', 10, $query_vector)
//  YIELD node, score
//  RETURN node.id, node.leaf_type, score;
//
//  // 2-hop graph: from a pipeline, find all leaf types it consumes
//  MATCH (p:Component {id: 'pipeline/research-entity'})-[:STEP_OF]->(:Component)-[:CONSUMES_LEAF_TYPE]->(t:LeafType)
//  RETURN DISTINCT t.id;
