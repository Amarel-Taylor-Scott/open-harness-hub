"""src.teleon.seeds.profession_capability_seeder — generalize the DueCare template (governed source registry +
screening + verification) from ONE vertical (migrant-worker recruitment) to ANY profession.

The insight (owner, 2026-06-20): DueCare is one INSTANCE of a general pattern — every regulated profession has its
own licensing registries, exclusion/sanctions lists, professional bodies, and currency-of-rule requirements that a
base model cannot reliably enumerate or keep current. So we SEED, per profession, the same governed capability
shape: license-verification · exclusion-screening · compliance-currency (+ profession-specific deterministic
capabilities). Occupation spine: O*NET (862 occupations / 19,200 tasks) + Stanford WORKBank's "R&D-Opportunity"
zone (high task-delegation desire × low current model capability) — the rigorous version of "scour Wikipedia for
professions". Each derived capability is a CANDIDATE (serves_truth=false, propose-only, discovery≠trust) and is
DURABLE: a registry/exclusion-list gap is structural (it does not close when the next model ships — the model
still has no live access to the authoritative source).

Pure + deterministic; Teleon-layer (never imports src.baltor). Seeds propose; they never serve truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field

OCCUPATION_SPINE = "O*NET SOC taxonomy + Stanford WORKBank (R&D-Opportunity zone = durable capability-gap negative space)"


@dataclass(frozen=True)
class Profession:
    slot: str
    label: str
    sector: str
    onet_soc: str                       # O*NET SOC code (the occupation-spine pointer)
    license_registry: str               # the authoritative licensing register (source class)
    exclusion_list: str                 # the relevant exclusion/sanctions/debarment list
    professional_body: str              # who sets the rules (for compliance-currency)
    profession_specific: tuple = ()      # (slot_suffix, capability, determinism_ceiling) extras


#: a representative cross-sector occupation set (extend from the O*NET spine). Migration is ONE row — DueCare.
PROFESSIONS: list[Profession] = [
    Profession("registered-nurse", "Registered Nurse", "healthcare", "29-1141",
               "state nursing board license registry (Nursys)", "OIG LEIE exclusions",
               "state board of nursing", (("scope-of-practice-rule", "is a procedure within the licensed scope of practice?", 0.9),)),
    Profession("pharmacist", "Pharmacist", "healthcare", "29-1051",
               "state board of pharmacy registry", "OIG LEIE + DEA registration status",
               "state board of pharmacy", (("controlled-substance-schedule", "deterministic DEA schedule lookup for a drug", 1.0),)),
    Profession("attorney", "Attorney", "legal", "23-1011",
               "state bar admission registry", "state bar disciplinary / disbarment list",
               "state bar association", (("court-deadline", "deterministic court-deadline calc (reuses court-deadline-calculator seed)", 1.0),)),
    Profession("cpa-accountant", "CPA / Accountant", "finance", "13-2011",
               "state board of accountancy registry", "PCAOB disciplinary + SEC bars",
               "state board of accountancy", ()),
    Profession("financial-advisor", "Financial Advisor", "finance", "13-2052",
               "FINRA BrokerCheck / SEC IAPD registry", "FINRA / SEC enforcement bars",
               "FINRA / SEC", ()),
    Profession("general-contractor", "General Contractor", "construction", "11-9021",
               "state contractor license board registry", "state debarment / suspended-contractor list",
               "state contractors board", (("permit-requirement", "is a permit required for this work class? (jurisdictional If-Statement)", 0.9),)),
    Profession("seafarer", "Seafarer", "maritime", "53-5021",
               "flag-state Certificate-of-Competency registry (BIMCO digital cert)", "Combined IUU vessel list",
               "flag state / IMO", (("port-state-control", "QR-verify a digital seafarer credential", 1.0),)),
    Profession("customs-broker", "Customs Broker", "trade", "13-1041",
               "CBP customs-broker license registry", "UFLPA / CBP forced-labor entity list",
               "US CBP", (("hts-classification", "deterministic HTS code lookup for a good", 0.85),)),
    Profession("recruitment-agency", "Overseas Recruitment Agency", "migration", "13-1071",
               "PH DMW / BD OEP licensed-agency registry (DueCare)", "OFAC SDN + World Bank debarred",
               "labor-migration authority", (("agency-recruits-for", "resolve agency→foreign-employer edges (DueCare entity-intel)", 0.9),)),
    Profession("physician", "Physician", "healthcare", "29-1228",
               "state medical board registry", "OIG LEIE + NPDB malpractice flags",
               "state medical board", ()),
    Profession("real-estate-broker", "Real-Estate Broker", "real-estate", "41-9021",
               "state real-estate commission registry", "state license revocation list",
               "state real-estate commission", ()),
    Profession("food-establishment", "Food Establishment Operator", "food-safety", "35-1012",
               "local health-department permit registry", "FDA warning letters / recalls",
               "local health department / FDA", (("inspection-grade-currency", "is the posted inspection grade current?", 0.9),)),
    Profession("insurance-producer", "Insurance Producer", "insurance", "41-3021",
               "state insurance-department producer registry", "state insurance enforcement actions",
               "state insurance department", ()),
    Profession("commercial-driver", "Commercial Driver", "transport", "53-3032",
               "FMCSA CDL / carrier registry", "FMCSA out-of-service / safety-rating list",
               "US FMCSA", (("hours-of-service-rule", "deterministic hours-of-service compliance check", 1.0),)),
    Profession("export-controlled-supplier", "Export-Controlled Supplier", "trade", "11-3061",
               "BIS exporter registry", "BIS Entity List + denied-persons",
               "US BIS", (("eccn-classification", "deterministic ECCN export-control classification lookup", 0.85),)),
]

#: the three governed capabilities EVERY regulated profession needs (the DueCare shape), with their determinism.
_BASE = (
    ("license-verification", "verify a practitioner/entity against the authoritative licensing registry", 1.0, "license_registry"),
    ("exclusion-screening", "screen against the profession's exclusion/sanctions/debarment list", 0.95, "exclusion_list"),
    ("compliance-currency", "is the governing rule/requirement CURRENT? (freshness / CDC vs the professional body)", 0.9, "professional_body"),
)


def derive_for(p: Profession) -> list[dict]:
    """Derive the governed capability CANDIDATES a profession needs (base shape + profession-specific)."""
    out = []
    for suffix, capability, det, src_field in _BASE:
        out.append({
            "capability_slot": f"{p.slot}-{suffix}", "profession": p.slot, "sector": p.sector,
            "onet_soc": p.onet_soc, "intent": capability, "authoritative_source": getattr(p, src_field),
            "determinism_ceiling": det,
            "gap_hypothesis": f"a base model cannot enumerate or keep current {p.label}'s authoritative {suffix.replace('-', ' ')} source",
            "durable": True,  # registry/exclusion access is a STRUCTURAL gap — it does not close as models improve
            "serves_truth": False, "candidate": True,
        })
    for suffix, capability, det in p.profession_specific:
        out.append({
            "capability_slot": f"{p.slot}-{suffix}", "profession": p.slot, "sector": p.sector,
            "onet_soc": p.onet_soc, "intent": capability, "authoritative_source": p.professional_body,
            "determinism_ceiling": det,
            "gap_hypothesis": f"{p.label}-specific: {capability}",
            "durable": True, "serves_truth": False, "candidate": True,
        })
    return out


def seed_professions() -> list[dict]:
    """Every profession's derived governed capability candidates (flattened)."""
    out = []
    for p in PROFESSIONS:
        out.extend(derive_for(p))
    return out


def build_feed() -> dict:
    cands = seed_professions()
    sectors = sorted({p.sector for p in PROFESSIONS})
    return {
        "feed_version": "DiscoveredCapabilityFeed.v1",
        "discovered_at": "2026-06-20",
        "discovery_method": f"profession-scale derivation from the DueCare template across the {OCCUPATION_SPINE}",
        "provenance": "DueCare (gemma4_comp) generalized beyond migrant-worker protection; occupation spine = O*NET + Stanford WORKBank.",
        "governance": ("CANDIDATES ONLY — discovery is not trust. Each profession derives the DueCare governed shape "
                       "(license-verification · exclusion-screening · compliance-currency + profession-specific). "
                       "Every capability is DURABLE (registry/exclusion access is a structural gap that does not "
                       "close as models improve) and serves_truth=false. Nothing is promoted."),
        "sectors": sectors, "n_professions": len(PROFESSIONS), "occupation_spine": OCCUPATION_SPINE,
        "candidates": cands,
    }
