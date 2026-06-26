<!--
  VOLATILE BY DESIGN — all regulatory clause numbers, URLs, and institutional facts
  are marked [verify] where they depend on the current state of Philippine, Indonesian,
  or Nigerian law that could not be confirmed against a live source in this session.
  Treat every dated fact as a snapshot; re-verify on cadence before citing in product.
  Safety stance: detection + routing + citations only. No evasion guidance. No PII.
-->

# Building-Safety Violation Detection in Developing-Country Contexts — Worked Example

**Motivating fixture:** Angeles City, Pampanga, Philippines (2026) — a nine-story
building approved by the local Office of the Building Official (OBO) for nine floors
allegedly had a tenth floor under construction or recently completed when a collapse
occurred trapping workers. Permit/floor-count discrepancy and possible failure to
secure a revised permit are under investigation by local authorities, DPWH, and
DILG. [Verify: investigation status and findings are live and subject to revision.]

**Domain:** construction safety / building code compliance
**Cell:** `PH × construction-building-safety × primary_regulator × 2026 × government_primary × violation-detection`
**Per-cell source registry:** `data/source-registry/ph-building-safety.json`

---

## 1. Why This Is a Structural Capability Gap

### 1a. The confabulation trap

Ask a base model: "What does Philippine building code Section 301 say about permits
for adding a floor to an existing nine-story building?" The model will produce a
confident, formally phrased answer that reads like a regulatory quote. It is almost
certainly fabricated, or a blend of OSHA/IBC (US codes) and vague Philippine
terminology, because:

- **Training data is sparse** (`sparse_data` mechanism). Philippine regulatory text —
  Presidential Decree 1096 (National Building Code), its Implementing Rules and
  Regulations (IRR), DPWH Department Orders amending the IRR — constitutes a tiny
  fraction of the model's training corpus. The model reverts to the nearest common
  neighbor: US or European building code language, fluently reworded.

- **Clause numbers shift between IRR revisions** (`volatile_fact` lift reason).
  Section references are numbered within the IRR, not in PD 1096 itself [verify],
  which means each Department Order that amends the IRR can renumber adjacent
  sections. A clause cited correctly for the 2004 IRR may be wrong for a 2015
  amendment. The model has no version-awareness; it outputs a single confident
  clause number.

- **The fluency trap.** The failure presents identically to a confident correct
  answer. There is nothing in the model's output that signals "this clause number
  is hallucinated." Detection requires a verifier, not just the model.

### 1b. The four structural lift reasons

**1. `embodiment_required` (tier 5 — human only)**

The dispositive fact — how many floors does the building *actually* have — cannot
be answered from any database. The approved permit says 9. The as-built count
requires a body on site: a licensed structural engineer or OBO inspector who
physically counts and measures stories. No crawler, RAG pipeline, or satellite
image analysis [verify coverage in PH] provides the legally authoritative
as-built floor count. This is the apex tool call: human site visit.

**2. `accountability_or_license` (tier 2–5)**

Under PD 1096 and its IRR [verify], building permit applications above a certain
floor count and structural complexity require sign-off by a PRC-licensed structural
engineer and/or architect [verify which designations apply at which thresholds].
The signature is a legally accountable professional act: the licensee can be sued,
disciplined, and have their license revoked by the PRC. A model cannot hold a PRC
license, cannot be named on a permit, and cannot accept legal accountability for
a structural assessment. This gap is permanent — it is not a text-prediction
advantage at all.

**3. `no_addressable_source` (tier 4)**

LGU building-permit records — the document that specifies the approved floor count
for the Angeles City building — are predominantly kept as:
- paper ledgers in the OBO counter room, or
- internal electronic records not exposed to any public API or portal.

There is no national building-permit database publicly queryable in the Philippines
as of this writing [verify]. Some Metro Manila cities have begun partial digitization
[verify]. For Angeles City, Pampanga specifically, a member of the public or an
automated system cannot query "what floor count was approved for building X?" without
physically going to the OBO counter and filing a request. No endpoint exists to point
a tool at.

**4. `volatile_fact` (structural by recency)**

Even where the approved floor count *is* digitized, it is not static: a building
owner can apply for a permit amendment (revised permit for additional floors), and
the amendment may or may not be recorded consistently across all LGU systems. The
authoritative record is the most recent approved permit on file at the OBO, which
can change between the time a system queries it and the time a site inspection
occurs. The volatile-fact lift reason means this must be retrieved and versioned at
query time — it can never be "known" in model weights.

### 1c. Gap durability score

Using `scripts/eval/reason_codes.py::gap_durability_score()`:
- Reason codes: `embodiment_required`, `accountability_or_license`,
  `no_addressable_source`, `volatile_fact` — all structural.
- Dominant retrievability tier: 4–5 (tier-4 for permit records; tier-5 for site
  inspection).
- Mechanisms: `channel_inaccessibility`, `sparse_data`.

Estimated durability score: **5.0 / 5.0** — the maximum. This gap will not close
when the next model ships because the gap is not a text-prediction shortfall at all.

---

## 2. Defensive Detection Component Sketch

The product goal is **detection of red flags and routing to the proper authority
with citations** — never how to evade codes, permits, or inspection. The component
sketch below uses the repo's seven-primitive vocabulary.

### 2a. Knowledge Corpus — Philippine building code and permit context

**Component type:** Knowledge Corpus
**Contents:**

- Full text of PD 1096 (National Building Code of the Philippines, 1977 — public
  domain) [verify public domain status; PD 1096 is a presidential decree, expected
  public domain in PH].
- IRR of PD 1096 — current version with amendment history. **Version-dated; every
  extract carries: IRR version/date, DPWH DO number if amended, retrieved_at.**
  [verify current IRR version date].
- Indexed provisions relevant to violation detection:
  - Permit requirement for new construction and material alterations [verify: PD 1096
    Section 301 or equivalent in current IRR].
  - Approved number of floors / stories as a permit-specified attribute [verify
    section reference].
  - Certificate of Occupancy requirement [verify: Section 307 or equivalent].
  - Building Official duties and authority to issue Stop-Work Orders [verify section].
  - Licensed professional sign-off thresholds by building height/use [verify].
  - Definition of "material alteration" that triggers a new/revised permit [verify].
- NSCP (National Structural Code of the Philippines) summary of seismic zone
  classification for Pampanga / Region III [verify current NSCP edition and zone
  map reference; Region III includes Clark/Angeles area].
- RA 11058 + DO 198 (OSH law and construction safety implementing rules) — summary
  of safety officer requirement by site size [verify DO number and thresholds].

**Retrievability tier:** 3 (PD 1096 and IRR text available as PDFs on lawphil.net,
chan robles, DPWH site [verify]; requires OCR/extraction — lossy but possible).
**CDC requirement:** Yes — IRR amendments are event-driven; each DPWH DO amending
the IRR must trigger re-ingestion and re-versioning of all affected section extracts.

### 2b. If Statement — floor-count discrepancy and structural red-flag rules

**Component type:** If Statement
**Trigger inputs:**

- `reported_floor_count` — as-built or reported actual floor count (from site
  inspection report, news source, or tip)
- `approved_floor_count` — from the permit record (requires human-router to
  obtain from OBO; NOT queryable automatically for most PH LGUs)
- `occupancy_status` — occupied / under construction / mixed
- `licensed_engineer_on_permit` — PRC license number from permit; lookup via
  PRC registry [verify PRC online lookup availability]
- `certificate_of_occupancy_present` — yes / no / expired
- `fsic_present` — Fire Safety Inspection Certificate (BFP) present / expired / absent

**Flag conditions (each triggers routing):**

```
IF reported_floor_count > approved_floor_count
THEN flag: FLOOR_COUNT_EXCESS
  citation: PD 1096 Section 301 [verify] — permit required for each story of
            construction; Section 208 [verify] — Building Official authority
            to issue Stop-Work Order for unpermitted construction.
  route_to: LGU Office of the Building Official (OBO), DPWH Regional Office

IF approved_floor_count IS NULL AND reported_floor_count >= 1
THEN flag: PERMIT_RECORD_UNVERIFIABLE
  note: Permit record not publicly queryable; human-router required.
  route_to: LGU OBO counter (physical FOI request)

IF licensed_engineer_on_permit IS NULL
   AND approved_floor_count > [threshold from IRR — verify]
THEN flag: MISSING_LICENSED_ENGINEER_SIGN_OFF
  citation: PD 1096 IRR Rule [verify rule and section] — buildings above [n]
            stories require sign-off by PRC-licensed structural engineer.
  route_to: PRC (license verification); LGU OBO (permit correction)

IF PRC_license_status(licensed_engineer_on_permit) IN ['suspended', 'revoked', 'expired']
THEN flag: INVALID_PROFESSIONAL_LICENSE_ON_PERMIT
  citation: PD 1096 IRR professional-sign-off requirement [verify].
            PRC resolution on license status [cite specific resolution if available].
  route_to: PRC Board of Civil Engineering; LGU OBO; DPWH Regional Office

IF certificate_of_occupancy_present = FALSE
   AND occupancy_status = 'occupied'
THEN flag: OCCUPIED_WITHOUT_CO
  citation: PD 1096 Section 307 [verify] — Certificate of Occupancy required
            before any building or portion thereof is used or occupied.
  route_to: LGU OBO

IF fsic_present IN [FALSE, 'expired']
   AND occupancy_status = 'occupied'
THEN flag: MISSING_OR_EXPIRED_FIRE_SAFETY_CERTIFICATE
  citation: RA 9514 (Fire Code of the Philippines) IRR [verify section] —
            FSIC required for occupied buildings above [threshold — verify].
  route_to: Bureau of Fire Protection (BFP) local district office

IF reported_floor_count >= 5
   AND safety_officer_accredited IS NULL OR FALSE
THEN flag: MISSING_ACCREDITED_SAFETY_OFFICER
  citation: RA 11058, DO 198 s. 2018 [verify] — construction sites above
            [worker count / floor threshold — verify] require PRC/DOLE-
            accredited safety officer.
  route_to: DOLE Regional Office (OSH division)
```

**Abstain condition:** If `approved_floor_count` cannot be verified (OBO record
not accessible), the If Statement MUST emit `PERMIT_RECORD_UNVERIFIABLE` and
route to human — it MUST NOT infer or estimate the approved count from any
model-generated guess. The model's output for an unresolved permit lookup is
not admissible as a fact input to the flag conditions.

### 2c. Action — route to building official / authority with citations

**Component type:** Action (routing persona / dispatcher)

**Inputs:** flag set from the If Statement above, case metadata (address, building
name, reported incident, tip source).

**Outputs:**

1. **Structured routing packet** for each flag:
   - Authority to contact (OBO name + address for the LGU in question; DPWH
     Regional Office III [verify address and contact]; PRC main office; BFP
     district; DOLE regional)
   - Specific statutory basis (PD 1096 section [verify], RA 11058, RA 9514,
     as applicable)
   - Recommended evidence to attach (permit copy if obtainable, as-built count
     from inspection report, PRC license printout, CO / FSIC copies)
   - Escalation path if LGU OBO is non-responsive (DILG regional office;
     DPWH regional; media escalation pathway is out of scope for this component)

2. **Confidence and verification gap disclosure** appended to every routing
   packet:
   - Which inputs were obtained from human-verified sources vs inferred or
     unverifiable
   - Which clause numbers are `[verify]` pending re-ingestion of the current
     IRR version
   - Timestamp + IRR version used for the Knowledge Corpus extract

3. **Review queue ticket** (high-risk path): when `FLOOR_COUNT_EXCESS` +
   `OCCUPIED_WITHOUT_CO` both fire simultaneously (compound violation with
   life-safety implications), the Action routes to the review queue before
   issuing the routing packet — a human reviewer confirms the flag inputs
   before the packet is sent.

---

## 3. Retrievability Tiers for This Cell

| Source | Tier | Why | Automation closes it? |
|---|---|---|---|
| PD 1096 full text (lawphil.net, chan robles) | 3 | Stable URL; PDF/HTML; OCR needed for some versions | Partially — lossy; verify against DPWH primary |
| IRR of PD 1096 (DPWH) | 3 | PDF on DPWH; no delta feed; amendment-chain tracking required | Partially — CDC required for each DPWH DO |
| NSCP (ASEP publication) | 3 | PDF; may be paywalled for current edition [verify] | Partial at best |
| PRC license registry | 2 | Web query form [verify]; individual lookup available | Yes for spot-check; no bulk feed |
| LGU OBO building permit records | 4 | Counter-only; no public digital portal for most LGUs | **No** |
| LGU / BFP Facebook announcements | 4 | Login-walled for crawl; ephemeral; editable | **No** |
| FSIC status (BFP) | 4 | No publicly queryable database [verify] | **No** |
| Site inspection (as-built floor count) | 5 | Requires physical presence | **No — human apex** |

**Where a human / verified publisher is explicitly required:**

- Any claim that the approved floor count was X must come from a human who has
  physically obtained the permit from the OBO counter, or a verified publisher
  (OBO official) who has signed the record.
- Any claim about the as-built floor count must come from a licensed structural
  engineer or OBO inspector who has been on site.
- Any routing packet based on these facts must note the source and the verifier's
  identity (PRC license number for the engineer; OBO official's name and position)
  in the provenance chain.

A routing packet assembled without these verifiers must be labelled
`confidence: low / unverified` and must not be treated as a formal report.

---

## 4. Generalization: Indonesia and Nigeria

### 4a. Indonesia — SNI codes, PBG/IMB permits, Bahasa low-resource

**Cell:** `ID × construction-building-safety × primary_regulator × 2026`

**Regulatory framework [verify all]:**
- **IMB → PBG transition (2021):** Indonesia replaced the Izin Mendirikan Bangunan
  (IMB — Building Construction Permit) with the Persetujuan Bangunan Gedung (PBG —
  Building Approval) under Government Regulation PP 16/2021 implementing Law
  28/2002 on Buildings (as amended by Law 11/2020 / Omnibus Law) [verify current
  status and implementing regulation numbers]. The transition introduced an
  online system (SIMBG — Sistem Informasi Manajemen Bangunan Gedung) for PBG
  applications [verify SIMBG coverage and public accessibility].
- **SNI (Standar Nasional Indonesia):** structural standards are SNI codes, managed
  by BSN (Badan Standardisasi Nasional) [verify]. SNI 1726 covers seismic loading;
  SNI 1727 covers structural loads [verify edition years]. These are the Indonesian
  equivalent of the NSCP/NSCP. SNI documents may require purchase [verify access
  policy].
- **Professional licensing:** Sertifikat Keahlian (SKA) / Sertifikat Keterampilan
  (SKT) issued by LPJK (Lembaga Pengembangan Jasa Konstruksi) [verify current
  body — LPJK was reorganized under the Ministry of Public Works PUPR] for
  construction professionals.

**Gap profile vs PH:**
- **Lower-resource language** (`sparse_data` mechanism is more severe): Bahasa
  Indonesia regulatory text is significantly less represented in base model training
  data than Philippine English-language regulatory text. Confabulation risk is
  higher.
- **SIMBG digitization** is a partial tier-2 improvement over the Philippines
  (if public lookup is genuinely available [verify]), but regional and kabupaten
  (district) office compliance with SIMBG is uneven [verify].
- **Tier-4 channel dominance** is comparable: local building office (Dinas PUPR
  kabupaten/kota) Facebook pages and WhatsApp contractor groups carry material
  announcements not on official portals.
- **Structural lift reasons are identical:** `embodiment_required` (site
  inspection of as-built floor count), `accountability_or_license` (SKA-holding
  professional sign-off), `no_addressable_source` (local PUPR records), `volatile_fact`
  (PBG amendment chain from IMB transition).

**Sources to add for ID cell [verify all]:**
- SIMBG portal (simbg.pu.go.id [verify]) — PBG status lookup
- BSN (bsn.go.id) — SNI standards (may be paywalled for current editions)
- Kementerian PUPR (pu.go.id) — implementing regulations, circulars
- LPJK or successor body — professional license registry [verify current body]
- Local Dinas PUPR pages (kabupaten/kota) — tier-4 (Facebook-primary)

### 4b. Nigeria — state building control, LASBCA (Lagos)

**Cell:** `NG × construction-building-safety × primary_regulator × 2026`

**Regulatory framework [verify all]:**
- Nigeria's building regulation is primarily **state-level** — there is no
  single federal building code equivalent to PD 1096. The National Building Code
  (NBC) was developed [verify adoption year; reportedly 2006 with updates] but
  adoption is state-by-state [verify].
- **Lagos:** the Lagos State Building Control Agency (LASBCA) issues building
  permits and enforcement actions in Lagos State [verify current mandate and
  website: lasbca.lagosstate.gov.ng or similar]. LASBCA has been the enforcement
  body for several high-profile building collapse responses in Lagos.
- **Other states:** Abuja / FCT uses the Federal Capital Development Authority
  (FCDA) or related body [verify current body name]; other states have varying
  degrees of Building Control Agency or works ministry capacity.

**Gap profile vs PH:**
- **State fragmentation** makes a single Knowledge Corpus impossible: each state's
  building code, permit format, approved-floor-count record system, and enforcement
  body are different. A component must be cell-specific to the state.
- **Lower digitization baseline** for permit records vs Philippines or Indonesia
  in most states [verify — Lagos is an exception with some digitization efforts].
- **Language fragmentation**: formal regulatory text is in English, but enforcement
  communication and contractor networks operate in Yoruba, Igbo, Hausa, and Pidgin
  English (Nigerian Pidgin), which models handle poorly (`sparse_data`).
- **Tier-4 dominance is severe**: in many Nigerian states, the authoritative building
  permit record is paper-only; the enforcement body's public communications are
  primarily Facebook and press releases; WhatsApp contractor networks carry
  informal enforcement signals [verify].

**Structural lift reasons:** identical set to PH — `embodiment_required`,
`accountability_or_license`, `no_addressable_source`, `volatile_fact` — with
the additional dimension that the Knowledge Corpus itself must be state-specific,
multiplying the acquisition surface.

**Sources for NG/Lagos cell [verify all]:**
- LASBCA (lasbca.lagosstate.gov.ph [verify correct domain]) — permits, Stop-Work
  orders, enforcement notices
- Lagos State Government Ministry of Physical Planning and Urban Development
  (mppud.lagosstate.gov.ng [verify]) — planning approvals
- FCDA / FCT Building Control — for Abuja [verify current body and URL]
- Council for the Regulation of Engineering in Nigeria (COREN) — professional
  license registry for engineers [coren.gov.ng — verify]
- NBC text (Standards Organisation of Nigeria / Federal Ministry of Works) —
  [verify current NBC edition and access method]

### 4c. The cross-jurisdiction pattern

The structural gap pattern is identical across PH, ID, and NG:

1. **Base model confabulates jurisdiction-specific code** (fluent, formally plausible,
   usually wrong or unverifiable).
2. **Permit records are predominantly tier-4** (counter-only, fragmented,
   non-digital).
3. **As-built verification is tier-5** (human site inspection only).
4. **Professional accountability is tier-2** (license registry queryable but
   no bulk feed; verification must be done for each permit individually).
5. **Tier-4 channel dominance** (Facebook / WhatsApp / oral networks carry
   enforcement signals the pipeline cannot ingest).

The reusable component pattern: `Knowledge Corpus (jurisdiction-specific code text)` +
`If Statement (floor-count and licensed-engineer gate)` + `Action (routing to
jurisdiction-specific authority)`. Only the Knowledge Corpus and the routing
targets change across jurisdictions. The If Statement logic and the abstain/
unverifiable gate are reusable.

---

## 5. Safety Stance

**What this component does:**

- Detects building-safety red flags: approved-floor-count vs actual, missing
  licensed-engineer sign-off, absent Certificate of Occupancy, expired FSIC,
  missing safety officer.
- Routes to the correct authority with citations to the relevant statute and
  section (flagged `[verify]` for all clause-level references).
- Discloses confidence level and verification gaps in every output.

**What this component does not do:**

- It does not advise how to obtain a permit without meeting code requirements.
- It does not advise how to avoid inspection.
- It does not advise on structural adequacy — that requires a licensed structural
  engineer's on-site assessment (tier-5; human apex tool call).
- It does not store any PII about building occupants, workers, or property owners.
- It does not publish the names of permit applicants or licensees except in the
  context of routing a specific verified complaint to the proper authority.

**Bias review requirement:**

Violation-detection components can over-flag: small informal builders in
lower-income areas may have less formal documentation (missing CO, no formal
safety officer record) while presenting lower actual structural risk than a
large formal project that has the paperwork but not the practice. The If Statement
must be calibrated against base rates, not just absence of documentation. This
requires a bias review before production deployment:
- False-positive rate for tier-4 / informal-documentation contexts vs tier-1
  formal-documentation contexts.
- Whether the routing action sends appropriate escalation for the documentation
  gap vs a structural-risk flag (these require different routing targets).

**Abstain rule:**

When the approved floor count cannot be verified from a human-verified source,
the component MUST emit `PERMIT_RECORD_UNVERIFIABLE` rather than infer a count.
A model-generated estimate of what the permit "probably said" is not admissible
as an input to the flag conditions. The confident-wrong failure mode in this
domain is life-safety consequential.

---

## 6. Component Registration Notes

**Primitives used:** Knowledge Corpus + If Statement + Action
**Cell:** PH × construction-building-safety (generalizes to ID, NG with
jurisdiction-specific Knowledge Corpus and routing targets)
**Lift reasons (all structural):** `embodiment_required`, `accountability_or_license`,
`no_addressable_source`, `volatile_fact`
**Durability class:** structural
**Estimated durability score:** 5.0 / 5.0
**Decay signal:** none (structural gaps do not close with next model)
**Source registry:** `data/source-registry/ph-building-safety.json`
**Promotion gate:** requires (a) current IRR version ingested and versioned,
(b) PRC license lookup integration confirmed, (c) bias review completed,
(d) legal review of routing-action outputs by jurisdiction.

---

*All `[verify]` markers indicate regulatory facts that are volatile by design
and were flagged during authoring as requiring confirmation against a current
primary source before production use. Do not strip these markers without
performing the verification and updating the provenance record.*
