"""src.teleon.training — learn the most efficient non-deterministic -> deterministic distillation paths.

The skills/distillation DATABASE (skills_db) turns the capability corpus + distillation records into a supervised
dataset; the POLICY (policy) trains a predictor that generalizes the best distillation strategy per capability and
is scored on held-out data, with a seam for a real trained model / LoRA. The harness (run_training) ties it
together and emits the model/LoRA artifact spec. Teleon-layer — never imports src.baltor; nothing here serves truth.
"""
from src.teleon.training.policy import (
    FittedPolicy,
    PriorPolicy,
    TrainedArtifactPolicy,
    evaluate,
    model_artifact_spec,
    run_training,
    train,
)
from src.teleon.training.capability_network import CapabilityNetwork, enrich_features
from src.teleon.training.skills_db import (
    FEATURE_KEYS,
    DistillationDataset,
    DistillationExample,
    build_dataset,
    feature_vector,
)

__all__ = [
    "feature_vector", "DistillationExample", "DistillationDataset", "build_dataset", "FEATURE_KEYS",
    "PriorPolicy", "FittedPolicy", "TrainedArtifactPolicy", "train", "evaluate", "model_artifact_spec",
    "run_training", "CapabilityNetwork", "enrich_features",
]
