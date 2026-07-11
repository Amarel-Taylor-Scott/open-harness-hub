-- OpenHubForAI canonical object count report.
--
-- This query intentionally separates curated manifest rows from generated
-- operational objects. Run after db/postgres/schema.sql and any loader job.

WITH counts AS (
  SELECT 'curated_manifest' AS object_family, 'component' AS relation_name, count(*)::bigint AS row_count FROM component
  UNION ALL
  SELECT 'source', 'source_record', count(*)::bigint FROM source_record
  UNION ALL
  SELECT 'generated_object', 'normalized_object', count(*)::bigint FROM normalized_object
  UNION ALL
  SELECT 'entity', 'canonical_entity', count(*)::bigint FROM canonical_entity
  UNION ALL
  SELECT 'entity_edge', 'object_entity_ref', count(*)::bigint FROM object_entity_ref
  UNION ALL
  SELECT 'dedupe', 'dedupe_cluster', count(*)::bigint FROM dedupe_cluster
  UNION ALL
  SELECT 'review', 'review_ticket', count(*)::bigint FROM review_ticket
  UNION ALL
  SELECT 'promotion', 'promotion_decision', count(*)::bigint FROM promotion_decision
  UNION ALL
  SELECT 'index', 'index_record', count(*)::bigint FROM index_record
  UNION ALL
  SELECT 'index', 'partition_manifest', count(*)::bigint FROM partition_manifest
  UNION ALL
  SELECT 'index', 'index_delta', count(*)::bigint FROM index_delta
  UNION ALL
  SELECT 'embedding', 'object_embedding', count(*)::bigint FROM object_embedding
  UNION ALL
  SELECT 'label', 'label_assignment', count(*)::bigint FROM label_assignment
  UNION ALL
  SELECT 'dimension', 'dimension_value', count(*)::bigint FROM dimension_value
)
SELECT
  object_family,
  relation_name,
  row_count
FROM counts
ORDER BY object_family, relation_name;
