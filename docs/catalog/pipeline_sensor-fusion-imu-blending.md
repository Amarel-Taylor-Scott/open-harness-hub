# Multi-sensor fusion (IMU + thermal + ToF) with model blending

*pipeline* · `pipeline/sensor-fusion-imu-blending` · v0.1.0 · stable

Multi-modal sensor-fusion pipeline for behavior / activity
classification: IMU (inertial measurement unit — accelerometer +
gyroscope), THM (thermal), ToF (time-of-flight depth). Train
separate per-sensor branches (1D-CNN + LSTM), then blend predictions
via weighted average / stacking. Standard for wearable / behavior-
detection competitions.

Verified by Open Harness Hub mining: hideyukizushi CMI25 IMU+THM/ToF
TF BlendingModel (625 votes, CMI Detect Behavior with Sensor Data),
sohier CMI 2025 Demo Submission (875 votes, same competition).

| axis | value |
|---|---|
| industry | healthcare, ai, manufacturing |
| capability | classification, extraction |
| modality | structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Per-sensor branch training (IMU/THM/ToF) + weighted blending.

**pipeline_kind:** `training_and_serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `train_branches` | processor | `processor/iterative-revise-loop` | — |
| 3 | `blend` | processor | `processor/multi-vector-fusion` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

