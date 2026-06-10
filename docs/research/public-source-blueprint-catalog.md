# Public Source Blueprint Catalog

Esoteric industry primitives should start with source blueprints, not raw
scrapes. A blueprint defines what kind of public source to look for, how to
capture it, which objects it can produce, and where review is required.

The first blueprint set covers:

- automotive title, registration, dealer, recall, and vehicle-condition
  evidence;
- labor and employment-agency fee rules, license checks, and placement
  checklists;
- municipal plumbing, HVAC, mechanical permit, inspection, and commissioning
  checklists;
- woodworking, millwork, shop traveler, finish schedule, and safety procedure
  sources;
- offshore oil and gas regulator guidance, incident notices, inspection
  evidence, environmental monitoring, and emergency procedures;
- environmental review notices, public comments, sampling plans, impact
  findings, and mitigation commitments.

## Blueprint Fields

Each source blueprint declares:

- source family and vertical;
- publisher class, trust tier, privacy boundary, and license posture;
- access method such as official web page, public dataset, form, PDF, API, or
  archive index;
- source examples as domain patterns or source-family descriptions, not copied
  protected content;
- expected objects and labels;
- required factory stages;
- review triggers.

## Worker Flow

Workers should run the same guarded path:

1. route source governance and license policy;
2. snapshot or locate archive captures;
3. convert pages/PDFs/forms to Markdown with source spans;
4. extract normalized objects;
5. link entities and jurisdictions;
6. fuzzy-dedupe candidate objects;
7. emit keyword, vector, graph, facet, freshness, and quality index records;
8. open review tickets for high-risk or volatile facts.

This creates a repeatable ingestion plan for public facts while avoiding
proprietary manuals, private job postings, customer records, emails, or PII in
the public catalog.
