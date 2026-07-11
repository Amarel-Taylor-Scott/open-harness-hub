"""Knowledge Corpus primitive — a store of facts queried by a trigger."""
from __future__ import annotations

from scripts.pipeline_object import PipelineObject
from scripts.primitives.base import Primitive


class KnowledgeCorpus(Primitive):
    kind = "knowledge_corpus"
    label = "Knowledge Corpus"
    stage = "Knowledge Corpus"
    exec_model = "static-information"
    description = ("A store of facts queried by a trigger (keyword / regex / vector RAG / exact-id / "
                   "classifier / graph); static or dynamically fetched, with provenance + freshness.")
    schema_types = ("knowledge-pack", "dataset")
    subtypes = {"dataset": "Dataset"}

    def _run(self, po: PipelineObject) -> PipelineObject:
        retrieve = self.config.get("retrieve", lambda _po: [])
        po.set(self.config.get("out_key", "knowledge"), retrieve(po))
        return po
