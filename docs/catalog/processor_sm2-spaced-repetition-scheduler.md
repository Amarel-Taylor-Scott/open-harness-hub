# SM-2 spaced-repetition scheduler for AI-generated flashcards

*processor* · `processor/sm2-spaced-repetition-scheduler` · v0.1.0 · stable

Deterministic SuperMemo SM-2 algorithm implementation that schedules
AI-generated flashcards for review. Takes a quality-of-recall score (0-5)
and the card's current SM-2 state (easiness factor, interval, repetitions)
and emits the next review date and updated state. Wrong answers (score < 3)
reset the card to same-day review; correct answers extend the interval by
the easiness factor. Designed to run entirely on-device without a network
call.

CAPABILITY LIFT (structural): a language model cannot reliably compute the
SM-2 formula deterministically — it samples, and the scheduling arithmetic
must be exact (the wrong interval wastes the learner's memory window or
burns it by reviewing too late). The algorithm is a deterministic verifier
outside the model. lift_reason: deterministic_guarantee; mechanism:
sub_token (exact arithmetic below the token boundary).

| axis | value |
|---|---|
| industry | education, education.k12, education.tutoring, cross_industry |
| capability | planning, verification, format_conversion |
| modality | structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



