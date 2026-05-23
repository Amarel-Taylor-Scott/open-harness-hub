import json, re, yaml
from pathlib import Path

def load_rules(path):
    with open(path) as f:
        pack = yaml.safe_load(f)
    return [(r["id"], r["category"], r["severity"], re.compile(r["pattern"])) for r in pack["rules"]]

def to_prose(obj, prefix=""):
    """Walk a JSON object and emit one prose-like line per leaf value."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_label = k.replace("_", " ")
            if isinstance(v, (str, int, float, bool)) and v not in (None, "", 0):
                out.append(f"{key_label}: {v}")
            else:
                out.extend(to_prose(v, key_label))
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                out.append(f"{prefix}: {item}" if prefix else item)
            elif isinstance(item, dict):
                out.extend(to_prose(item, prefix))
    elif isinstance(obj, str):
        if obj.strip():
            out.append(f"{prefix}: {obj}" if prefix else obj)
    return out

PACKS = {
    "S (forced-labor)":    "catalog/rule-packs/grep/esg-forced-labor-red-flags.yaml",
    "E (environmental)":   "catalog/rule-packs/grep/esg-environmental-red-flags.yaml",
    "G (governance)":      "catalog/rule-packs/grep/esg-governance-red-flags.yaml",
}

samples = sorted(Path("data/supplier-disclosure-samples").glob("*.json"))
all_lines_for_sample = {}
results = {}
for sample_path in samples:
    sample = json.loads(sample_path.read_text())
    prose_lines = to_prose(sample)
    sample_prose = "\n".join(prose_lines)
    all_lines_for_sample[sample_path.name] = sample_prose
    sample_results = {}
    for pack_label, pack_path in PACKS.items():
        rules = load_rules(pack_path)
        hits = []
        for rule_id, category, severity, pat in rules:
            matches = pat.findall(sample_prose)
            if matches:
                hits.append({"rule": rule_id, "category": category, "severity": severity, "match_count": len(matches), "sample": str(matches[0])[:80]})
        sample_results[pack_label] = hits
    results[sample_path.name] = sample_results

for sample_name, sample_results in results.items():
    print(f"\n=== {sample_name} ===")
    for pack_label, hits in sample_results.items():
        if not hits:
            print(f"  {pack_label}: no hits")
            continue
        by_sev = {}
        for h in hits:
            by_sev.setdefault(h["severity"], []).append(f"{h['rule']}")
        print(f"  {pack_label}: {len(hits)} rules fired")
        for sev in ["critical", "high", "medium", "low"]:
            if sev in by_sev:
                print(f"     {sev:9s}: {', '.join(by_sev[sev])}")

print("\n=== headline ===")
for n, r in results.items():
    by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for hits in r.values():
        for h in hits:
            by_sev[h["severity"]] += 1
    print(f"  {n[:55]:55s}  C:{by_sev['critical']:>2}  H:{by_sev['high']:>2}  M:{by_sev['medium']:>2}  L:{by_sev['low']:>2}  total {sum(by_sev.values())}")

Path("/tmp/esg-grep-findings.json").write_text(json.dumps(results, indent=2))
