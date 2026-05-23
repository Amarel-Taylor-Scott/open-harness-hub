# Elasticsearch / OpenSearch index templates — Open Harness Hub

Use Elasticsearch (or OpenSearch, the API-compatible fork) when:

- You need **BM25 full-text retrieval** at scale (the canonical RAG
  retrieval baseline).
- You want **hybrid search** combining BM25 + dense vectors via
  Reciprocal Rank Fusion.
- You already run Elastic for logs and want a single search backend.

## Index: `oh-artifact`

One doc per artifact. Searchable by name, description, tags, and the
full manifest body.

```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "ohh_default": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "english_stemmer", "asciifolding"]
        }
      },
      "filter": {
        "english_stemmer": { "type": "stemmer", "language": "english" }
      }
    }
  },
  "mappings": {
    "properties": {
      "id":             { "type": "keyword" },
      "type":           { "type": "keyword" },
      "version":        { "type": "keyword" },
      "name":           { "type": "text", "analyzer": "ohh_default", "fields": { "keyword": { "type": "keyword" } } },
      "description":    { "type": "text", "analyzer": "ohh_default" },
      "license":        { "type": "keyword" },
      "lifecycle":      { "type": "keyword" },
      "lifecycle_position": { "type": "keyword" },
      "trust_boundary": { "type": "keyword" },
      "industry":       { "type": "keyword" },
      "capability":     { "type": "keyword" },
      "modality":       { "type": "keyword" },
      "tags":           { "type": "keyword" },
      "created":        { "type": "date" },
      "updated":        { "type": "date" },
      "body":           { "type": "object", "enabled": false },
      "embedding":      { "type": "dense_vector", "dims": 384, "index": true, "similarity": "cosine" }
    }
  }
}
```

## Index: `oh-knowledge`

One doc per knowledge leaf — RAG retrieval target.

```json
{
  "mappings": {
    "properties": {
      "leaf_id":    { "type": "keyword" },
      "pack_id":    { "type": "keyword" },
      "leaf_type":  { "type": "keyword" },
      "industry":   { "type": "keyword" },
      "language":   { "type": "keyword" },
      "text":       { "type": "text", "analyzer": "ohh_default" },
      "embedding":  { "type": "dense_vector", "dims": 384, "index": true, "similarity": "cosine" },
      "metadata":   { "type": "object", "enabled": false }
    }
  }
}
```

## Hybrid query (BM25 + dense + RRF)

```json
POST oh-knowledge/_search
{
  "size": 10,
  "rank": { "rrf": { "window_size": 50, "rank_constant": 60 } },
  "query":      { "match": { "text": { "query": "thunderclap headache" } } },
  "knn":        { "field": "embedding",
                  "query_vector": [/* 384 floats */],
                  "k": 10, "num_candidates": 100,
                  "filter": { "term": { "industry": "healthcare.clinical" } } }
}
```

## Loader

`scripts/db/load_elasticsearch.py` (TBA) walks every manifest under
`catalog/`, computes embeddings via the configured processor
(`processor/embedder-minilm` by default), and bulk-indexes to
`oh-artifact` + `oh-knowledge`. Idempotent on re-run.

## OpenSearch differences

OpenSearch >= 2.10 has identical query syntax for BM25 and HNSW vector
search. RRF is supported as of OpenSearch 2.12; earlier versions need
hybrid query DSL. Otherwise the schemas above work as-is.
