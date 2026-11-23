# SPDX-License-Identifier: Apache-2.0
"""Conformance suite: mutations of the valid examples that a validator must refuse, and the precedence cases
(SPEC 8.2). Run: python tools/conformance/mutation_cases.py   (exit 0 = all expectations met)."""
import copy, json, pathlib, sys
D = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(D / "tools"))
import check_dossier as cd
V = cd.load_vocab(D / "vocab"); schema = json.loads((D / "schema/dossier.schema.json").read_text())
L = lambda n: json.loads((D / "examples" / n).read_text())
def prop(d, id): return next(p for p in d["properties"] if p["id"] == id)
cases = []
def case(name, base, mutate, expect, sources=None):
    d = copy.deepcopy(base); mutate(d)
    R, _ = cd.check(d, V, schema, sources)
    hit = [e for e in R.errors if expect in e]
    cases.append((name, bool(hit)))
    print(("PASS" if hit else "MISS"), name, "->", (hit or R.errors or ["no error"])[0][:150])
e1, e2, e3, e4, e5 = (L(n) for n in ("01-humectant-active.json", "02-rheology-modifier.json", "03-uv-filter.json", "04-extracted-emollient.json", "05-minimal-l1-curated.json"))
src = D / "examples/sources"
case("unknown top-level key", e1, lambda d: d.update(runbook_id="x"), "schema")
case("numeric value without unit", e1, lambda d: prop(d, "use-level").pop("unit"), "schema")
case("two value forms at once", e1, lambda d: prop(d, "use-level")["value"].update(exact=3), "schema")
case("regulatory limit without region", e3, lambda d: prop(d, "reg-eu").pop("scope"), "schema")
case("restricted element in the public representation", e1, lambda d: d["statements"][0].update(visibility="restricted"), "schema")
case("property key not in vocabulary", e1, lambda d: prop(d, "use-level").update(key="use.levle"), "not in vocabulary")
case("unit of the wrong dimension", e1, lambda d: prop(d, "use-level").update(unit="mPa.s"), "not accepted")
case("implausible use level (500 %)", e1, lambda d: prop(d, "use-level")["value"]["range"].update(max=500), "plausible")
case("pH 15", e1, lambda d: prop(d, "use-ph")["value"]["range"].update(max=15), "plausible")
case("nominal code from the wrong set", e1, lambda d: prop(d, "form")["value"].update(nominal="humectant"), "nominal code")
case("SPF without a test formulation", e3, lambda d: prop(d, "spf-f1").update(subject={"kind": "neat"}), "tied to a test formulation")
case("SPF with partially disclosed formulation", e3, lambda d: d["formulations"][0].update(disclosure="partial"), "disclose every UV filter")
case("SPF without method", e3, lambda d: prop(d, "spf-f1").pop("method"), "method.standard")
case("SPF boost without comparator", e3, lambda d: prop(d, "spf-boost").pop("comparison"), "comparator")
case("efficacy result without outcome", e1, lambda d: prop(d, "eff-tewl").pop("outcome"), "outcome is required")
case("viscosity of a dispersion without shear conditions", e2, lambda d: prop(d, "spec-visc").update(method={"instrument": "Viscometer"}), "shear_rate or rotation_speed")
case("dangling reference", e1, lambda d: prop(d, "eff-tewl").update(study="st-missing"), "does not resolve")
case("formulation not adding up", e2, lambda d: [(l.pop("qs"), l.update(percent=10)) for l in d["formulations"][0]["lines"] if l.get("qs")], "add up to 100")
case("composition minima above 100", e1, lambda d: d["composition"]["components"][0].update(content={"range": {"min": 90, "max": 95}}), "minimum contents")
case("L3 claim with a figure-only dataset", e3, lambda d: d.update(conformance_level="L3"), "claims L3")
case("L2 claim on a minimal dossier", e5, lambda d: d.update(conformance_level="L2"), "claims L2")
case("minimal dossier without phase", e5, lambda d: d.update(properties=[p for p in d["properties"] if p["key"] != "use.phase"]), "below L1")
case("curated flag in a manufacturer dossier", e1, lambda d: d["statements"][0].update(curated=True), "curated: true is allowed only")
case("expired-style certificate without valid_until", e1, lambda d: next(a for a in d["attestations"] if a["id"] == "att-cosmos").update(status="certified") or next(a for a in d["attestations"] if a["id"] == "att-cosmos").pop("valid_until"), "needs issuer and valid_until")
case("extracted element without evidence", e4, lambda d: prop(d, "shelf").pop("evidence"), "schema", src)
case("extracted number not in its quote", e4, lambda d: prop(d, "spec-acid")["value"]["limit"].update(value=0.2), "in none of its quotes", src)
case("extracted quote not on the page", e4, lambda d: prop(d, "shelf")["evidence"][0].update(quote="Shelf life: 24 months from delivery."), "not verbatim", src)
case("extracted leaf not covered", e4, lambda d: prop(d, "typ-density")["evidence"][0].update(supports=["/value"]), "no evidence covers", src)
case("extracted limit turned into a different operator", e4, lambda d: prop(d, "spec-water")["value"]["limit"].update(op=">="), "limit operator", src)
case("extracted dataset with points", e4, lambda d: d["datasets"][0].update(points_origin="publisher_raw"), "schema", src)
case("extracted CAS number not in its quote", e4, lambda d: d["identity"].update(cas=["9999-99-9"]), "identifier '9999-99-9'", src)
case("extracted trade name not in its quote", e4, lambda d: d["identity"].update(trade_name="Exaester GX"), "identifier 'Exaester GX'", src)
case("thousands separator proves nothing", e4, lambda d: (prop(d, "typ-spread")["value"].update(exact=2.5), prop(d, "typ-spread")["evidence"][0].update(quote="approx. 2,500 mm²/10 min")), "in none of its quotes")
e6 = L("06-extracted-silver-chloride-tio2.json")
case("basis content without analyte", e6, lambda d: prop(d, "basis-ag").pop("analyte"), "composition.regulated_basis_content needs analyte", src)
case("analyte code not in the vocabulary", e6, lambda d: prop(d, "basis-ag").update(analyte={"code": "element.xx"}), "analyte code 'element.xx' not in vocabulary regulated-bases", src)
case("analyte on a key without one", e6, lambda d: prop(d, "spec-water").update(analyte={"code": "element.ag"}), "analyte is not allowed for physchem.water_content", src)
case("basis content of a dilution", e6, lambda d: prop(d, "basis-ag").update(subject={"kind": "dilution", "medium": "water", "material_conc": {"value": 10, "unit": "%", "basis": "as_supplied"}}), "is stated for the material as supplied (subject neat)", src)
case("basis content as a recommendation", e6, lambda d: prop(d, "basis-ag").update(basis="recommended"), "basis recommended is not allowed for composition.regulated_basis_content", src)
case("basis content with a scope", e6, lambda d: prop(d, "basis-ag").update(scope={"region": ["EU"]}), "takes no scope or conditions", src)
case("analyte not covered by evidence", e6, lambda d: prop(d, "basis-ag")["evidence"][0].update(supports=["/value", "/unit"]), "no evidence covers /analyte", src)
case("quote does not name the analyte", e6, lambda d: (prop(d, "basis-ag").update(value={"limit": {"op": "<=", "value": 2.5}}), prop(d, "basis-ag")["evidence"][0].update(quote="max. 2.5 %")), "the analyte element.ag", src)
case("ISO 16128 index above 100 % (158 % is 1.58 in the canonical unit 1)", e1, lambda d: prop(d, "noi").update(unit="%", value={"exact": 158}), "plausible")
print()
m, x, c = e1, e4, e5
m2 = copy.deepcopy(m); m2["version"] += 1
dist = copy.deepcopy(m); dist["source"] = {"route": "distributor", "publisher": {"name": "Example Distribution GmbH", "domain": "distributor.example.net"}}
for name, a, b, want in (("extracted replaces curated", c, x, True), ("curated replaces extracted", x, c, False),
                         ("manufacturer replaces extracted", x, m, True), ("extracted replaces manufacturer", m, x, False),
                         ("distributor replaces manufacturer", m, dist, False), ("manufacturer replaces distributor", dist, m, True),
                         ("newer manufacturer version replaces older", m, m2, True), ("older manufacturer version replaces newer", m2, m, False)):
    got, why = cd.may_replace(a, b); cases.append((name, got == want)); print("PASS" if got == want else "MISS", f"precedence: {name} -> {got} ({why})")
bad = sum(1 for _, ok in cases if not ok); print(f"\n{len(cases) - bad}/{len(cases)} expectations met")
# The Annex basis phrases (not counted above): each phrase of the compiled list appears once in the map, with the
# same entries, and maps to a regulated-bases key, "stoichiometric" or "not_a_basis".
C = D / "tools/conformance"
md = {}
for line in (C / "annex-basis-phrases-2026-11-16.md").read_text(encoding="utf-8").splitlines():
    if line.startswith("| `"):
        cells = [x.strip() for x in line.strip("|").split("|")]
        md[cells[0].strip("`")] = [x.strip() for x in cells[1].split(",")]
pm = json.loads((C / "regulated_basis_phrases.json").read_text(encoding="utf-8"))["phrases"]
targets = set(V["regulated-bases"]["_keys"]) | {"stoichiometric", "not_a_basis"}
seen = [p["phrase"] for p in pm]
problems = [f"'{p}' is {seen.count(p)} times in the map" for p in md if seen.count(p) != 1]
problems += [f"'{p}' is not in the compiled list" for p in seen if p not in md]
problems += [f"'{p['phrase']}': entries differ" for p in pm if p["phrase"] in md and p["entries"] != md[p["phrase"]]]
problems += [f"'{p['phrase']}' maps to unknown '{p['maps_to']}'" for p in pm if p["maps_to"] not in targets]
print(("PASS" if not problems else "MISS"), f"phrase map: {len(md)} phrases, {len(pm)} entries ->", "; ".join(problems) or "all mapped")
# Rule 6 vectors (not counted above): each quote, covering /analyte of a basis-content property, through check_evidence.
def rule6_names(quote, code):
    el = {"id": "v", "key": "composition.regulated_basis_content", "analyte": {"code": code},
          "evidence": [{"source": "doc", "page": 1, "quote": quote, "supports": ["/analyte"]}]}
    R = cd.Report()
    cd.check_evidence("/v", el, V, {"doc": {"kind": "source_document"}}, None, R)
    return not any("the analyte" in e or "/analyte" in e for e in R.errors)
vec = json.loads((C / "rule6_vectors.json").read_text(encoding="utf-8"))["vectors"]
failed = [v for v in vec if rule6_names(v["quote"], v["code"]) != v["expect"]]
for v in failed:
    print("MISS rule6 vector:", v["quote"], v["code"], "expected", v["expect"], "-", v["why"])
print(("PASS" if not failed else "MISS"), f"rule6 vectors: {len(vec) - len(failed)} passed, {len(failed)} failed")
# Empty lists (not counted above): an empty `conditions` on a basis-content property counts as absent (SPEC 6.3).
d6 = copy.deepcopy(e6); prop(d6, "basis-ag")["conditions"] = []
R6, _ = cd.check(d6, V, schema, src)
empty_ok = not R6.errors
print(("PASS" if empty_ok else "MISS"), "empty conditions on basis content ->", (R6.errors or ["no error"])[0][:150])
sys.exit(1 if bad or problems or failed or not empty_ok else 0)
