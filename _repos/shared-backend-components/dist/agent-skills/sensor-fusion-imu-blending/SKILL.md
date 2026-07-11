---
name: sensor-fusion-imu-blending
description: Per-sensor branch training (IMU/THM/ToF) + weighted blending.
when_to_use: 'Pipeline kind: training_and_serving.'
---

# Multi-sensor fusion (IMU + thermal + ToF) with model blending

Multi-modal sensor-fusion pipeline for behavior / activity
classification: IMU (inertial measurement unit — accelerometer +
gyroscope), THM (thermal), ToF (time-of-flight depth). Train
separate per-sensor branches (1D-CNN + LSTM), then blend predictions
via weighted average / stacking. Standard for wearable / behavior-
detection competitions.

Verified by OpenHubForAI mining: hideyukizushi CMI25 IMU+THM/ToF
TF BlendingModel (625 votes, CMI Detect Behavior with Sensor Data),
sohier CMI 2025 Demo Submission (875 votes, same competition).

## Task

Per-sensor branch training (IMU/THM/ToF) + weighted blending.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **train_branches** — `processor` → `processor/iterative-revise-loop`
3. **blend** — `processor` → `processor/multi-vector-fusion`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub component: `pipeline/sensor-fusion-imu-blending` v0.1.0
- License: `MIT`
- Industry: healthcare, ai, manufacturing
- Full source manifest: see `references/manifest.yaml`
