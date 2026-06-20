# Community Moderation Knowledge Objects

Social platforms, group chats, forums, marketplaces, creator communities, and
local neighborhood groups all run on repeatable moderation procedures. Those
procedures are good candidates for knowledge objects because they combine
policy text, escalation rules, evidence checklists, appeal workflows, moderator
questions, and review queues.

The useful primitive is not just a toxicity classifier. It is a structured
pipeline that asks:

- Which community rule or platform policy might apply?
- What evidence is needed before action?
- Is the item spam, harassment, scam, impersonation, unsafe solicitation,
  marketplace abuse, misinformation, or a local group-rule issue?
- Does the case require safety, legal, publisher, or domain-expert review?
- What can be safely automated, and what must be routed to a human moderator?
- What explanation, appeal path, and audit record should be emitted?

## Knowledge Object Families

- community rule object;
- moderator checklist item;
- escalation trigger;
- appeal review question;
- evidence requirement;
- policy-to-action mapping;
- safety handoff route;
- group-specific norm or posting requirement;
- transparency-log event;
- repeat-offender or coordinated-abuse signal.

## Guardrails

These objects should be written for defense, review, and governance. They
should not include instructions for evading moderation, grooming, fraud, spam,
or harassment. High-risk child-safety, self-harm, exploitation, violent threat,
or privacy cases should be routed to specialized review and legal/safety
processes instead of being auto-actioned from a generic model response.
