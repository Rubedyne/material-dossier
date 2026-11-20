#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Reference checker for the Rubedyne Material Dossier standard 1.0 (non-normative).

SPEC.md is the authority; where this script and SPEC.md disagree, SPEC.md wins.

    check_dossier.py DOSSIER.json [...]            schema + rules of SPEC section 11
    check_dossier.py --sources DIR DOSSIER.json    also verify evidence quotes against
                                                   DIR/<media id>.p<page>.txt
    check_dossier.py --usage-view DOSSIER.json     print the usage view (SPEC 6.1) as JSON
    check_dossier.py --index INDEX.json            check an index and the hashes of the
                                                   dossier files that sit next to it

Needs Python 3.9+ and the `jsonschema` package (Draft 2020-12).
Exit status: 0 = no errors, 1 = errors, 2 = usage problem.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARRAYS = ("properties", "datasets", "formulations", "studies", "relations",
          "attestations", "statements", "media")
RANK = {"manufacturer": 4, "distributor": 3, "extracted": 2, "curated": 1}
NUMERIC_FORMS = ("exact", "range", "limit")
# The bases a property of a key with an analyte (SPEC 5.5.6, 6.3) may have.
ANALYTE_BASES = ("specification", "declared", "typical", "measured")
# Members that are classification, structure or references: no evidence needed (SPEC 7.3).
EXEMPT = {"id", "as_of", "visibility", "curated", "note", "evidence", "key", "basis",
          "outcome", "kind", "role", "study", "formulation", "figure", "report",
          "document", "supports", "support", "refines", "points_origin", "type",
          "scale", "as_written", "significant", "effect", "scheme", "status",
          "disclosure", "is_subject", "change", "vs", "ref", "code", "in_figure",
          "source_language", "complete", "non_standard", "all_endpoints_reported",
          "license", "sha256", "mime", "bytes", "url", "rank", "of", "product_type",
          "product_form", "phase", "function"}
# Identifier members of the identity and of composition components: their text value must occur in a quote that
# covers it (SPEC 7.3 rule 5). Pointers are relative to the element.
IDENTIFIER_PATHS = {
    "/identity": re.compile(r"/(trade_name|product_code|grade|chemical_name|molecular_formula|family/(name|id)"
                            r"|manufacturer/name|(inci|cas|ec|synonyms)/\d+|inci_variants/\d+/names/\d+)"),
    "/composition/components/": re.compile(r"/(inci|name|(cas|ec)/\d+|origin/botanical/latin_name)"),
}
LIMIT_WORDS = {
    "<=": ("≤", "<=", "max", "up to", "not more than", "at most", "nmt", "maximum", "<"),
    "<": ("<", "less than", "below", "under"),
    ">=": ("≥", ">=", "min", "at least", "not less than", "nlt", "minimum", ">"),
    ">": (">", "more than", "above", "greater than", "over"),
}


# ----------------------------------------------------------------- loading
def load_vocab(vocab_dir: Path) -> dict:
    out = {}
    for f in sorted(vocab_dir.glob("*.json")):
        if f.name == "index.json":
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        data["_keys"] = {t["key"]: t for t in data["terms"]}
        out[data["vocab"]] = data
    return out


def is_x(key) -> bool:
    return isinstance(key, str) and key.startswith("x-")


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


# ----------------------------------------------------------------- helpers
def elements(doc):
    for arr in ARRAYS:
        for i, el in enumerate(doc.get(arr, [])):
            yield arr, i, el


def conditions_of(*holders):
    out = []
    for h in holders:
        if not h:
            continue
        out += h.get("conditions", [])
        out += (h.get("method") or {}).get("settings", [])
    return out


def numbers_of(value: dict):
    if "exact" in value:
        return [value["exact"]]
    if "range" in value:
        return [value["range"]["min"], value["range"]["max"]]
    if "limit" in value:
        return [value["limit"]["value"]]
    return []


def in_vocab(V, name, key):
    return key in V[name]["_keys"]


def nominal_ok(V, set_name, code):
    if set_name in V:
        return code in V[set_name]["_keys"]
    s = V["nominal-codes"]["_keys"].get(set_name)
    return bool(s) and code in s["codes"]


def key_term(V, key):
    """The property-keys term for a key, resolving the efficacy.* pattern."""
    t = V["property-keys"]["_keys"].get(key)
    if t:
        return t
    if key.startswith("efficacy.") and key[9:] in V["endpoints"]["_keys"]:
        return V["property-keys"]["_keys"]["efficacy.*"]
    return None


def unit_dim(V, dim):
    return V["units"]["_keys"].get(dim) if dim else None


# ----------------------------------------------------------------- usage view (SPEC 6.1)
def usage_view(doc: dict, V: dict) -> tuple[dict, list]:
    """The usage view and the list of reasons it is incomplete (empty = complete)."""
    lang = doc.get("default_language", "en")

    def general(p, key):
        return (p.get("key") == key and p.get("basis") == "recommended"
                and p.get("subject", {}).get("kind") == "neat"
                and "scope" not in p and not p.get("conditions"))

    props = doc.get("properties", [])
    view, missing = {}, []
    usage = {}
    for p in props:
        if general(p, "use.level"):
            v = p["value"]
            if "range" in v:
                usage["min"], usage["max"] = v["range"]["min"], v["range"]["max"]
            elif "limit" in v and v["limit"]["op"] in ("<=", "<"):
                usage["max"] = v["limit"]["value"]
            elif "exact" in v:
                usage["min"] = usage["max"] = v["exact"]
            break
    for p in props:
        if general(p, "use.level_typical") and "exact" in p["value"]:
            usage["typical"] = p["value"]["exact"]
            break
    if "max" in usage:
        view["usage"] = usage
    else:
        missing.append("no general recommended use.level with an upper bound")

    stages = V["process-stages"]["_keys"]
    letters = []
    for p in props:
        if general(p, "use.phase") and "nominal" in p["value"]:
            letter = stages.get(p["value"]["nominal"], {}).get("usage_view_phase")
            if letter and letter not in letters:
                letters.append(letter)
    cold = any(general(p, "use.phase") and "nominal" in p["value"]
               and stages.get(p["value"]["nominal"], {}).get("usage_view_process") == "cold"
               for p in props)
    if letters:
        view["phase"] = letters
    if cold:
        view["process"] = "cold"
    if not letters and not cold:
        missing.append("no use.phase that maps to a phase letter or to process cold")

    for p in props:
        if general(p, "use.ph_window"):
            v, w = p["value"], {}
            if "range" in v:
                w = {"min": v["range"]["min"], "max": v["range"]["max"]}
            elif "limit" in v:
                w = {"max" if v["limit"]["op"] in ("<=", "<") else "min": v["limit"]["value"]}
            if w:
                view["ph_window"] = w
            break
    for p in props:
        if general(p, "use.process_temperature_max"):
            v = p["value"]
            if "exact" in v:
                view["temperature"] = {"max": v["exact"]}
            elif "limit" in v and v["limit"]["op"] in ("<=", "<"):
                view["temperature"] = {"max": v["limit"]["value"]}
            break
    for kind in ("guidance", "checklist"):
        lines = [" ".join(s["text"][lang].split()) for s in doc.get("statements", [])
                 if s.get("kind") == kind and "scope" not in s and lang in s.get("text", {})]
        if lines:
            view[kind] = lines[:6]
    return view, missing


# ----------------------------------------------------------------- evidence (SPEC 7.3)
def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("­", "")
    text = re.sub(r"-\s*\n\s*", "", text)
    return " ".join(text.split()).casefold()


_NUM = re.compile(r"\d+(?:[.,]\d+)*")


def number_in_quote(n, quote: str) -> bool:
    for tok in _NUM.findall(quote):
        if re.fullmatch(r"[1-9]\d{0,2}(,\d{3})+", tok):
            continue  # "2,500": thousands or decimal? An ambiguous token proves nothing.
        if tok.count(",") + tok.count(".") > 1:
            continue
        try:
            if abs(float(tok.replace(",", ".")) - float(n)) < 1e-9:
                return True
        except ValueError:
            pass
    return False


def has_word(quote: str, word: str) -> bool:
    """`word` in the quote; a word made of letters must stand alone ("min" is not in "10 minutes")."""
    if not word[0].isalpha():
        return word in quote
    return re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", quote.casefold()) is not None


_NOT_ALNUM_BEFORE, _NOT_ALNUM_AFTER = r"(?<![^\W_])", r"(?![^\W_])"


def has_symbol(quote: str, symbol: str) -> bool:
    """`symbol` ("Ag", "AgCl") in the NFKC-normalised quote, case-sensitive, not next to a letter or digit."""
    text = unicodedata.normalize("NFKC", quote)
    return re.search(_NOT_ALNUM_BEFORE + re.escape(symbol) + _NOT_ALNUM_AFTER, text) is not None


def has_alias(quote: str, alias: str) -> bool:
    """A lower-case `alias` ("silver") in the normalised quote, not next to a letter or digit."""
    return re.search(_NOT_ALNUM_BEFORE + re.escape(alias) + _NOT_ALNUM_AFTER, norm(quote)) is not None


def analyte_term(V, key, code):
    """The term of an analyte code in the vocabulary its property key names; None when there is none to check."""
    t = key_term(V, key) if isinstance(key, str) and not is_x(key) else None
    name = (t or {}).get("analyte")
    return V.get(name, {}).get("_keys", {}).get(code) if name else None


def leaves(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in EXEMPT or k.startswith("x-"):
                continue
            yield from leaves(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaves(v, f"{path}/{i}")
    else:
        yield path, node


def check_evidence(where, el, V, media, sources, R):
    if el.get("curated") is True:
        return
    ev = el.get("evidence", [])
    aliases = V["units"].get("aliases", {})
    for i, e in enumerate(ev):
        m = media.get(e["source"])
        if not m or m.get("kind") != "source_document":
            R.err(where, f"evidence[{i}].source '{e['source']}' is not a source_document media element")
        pages = (m or {}).get("document", {}).get("pages")
        if pages and e["page"] > pages:
            R.err(where, f"evidence[{i}].page {e['page']} is beyond the document's {pages} pages")
        if sources is not None:
            f = sources / f"{e['source']}.p{e['page']}.txt"
            if not f.exists():
                R.err(where, f"evidence[{i}]: no source text {f.name}")
            elif norm(e["quote"]) not in norm(f.read_text(encoding="utf-8")):
                R.err(where, f"evidence[{i}]: quote is not verbatim on page {e['page']} of '{e['source']}'")
    for ptr, val in leaves(el):
        quotes = [e["quote"] for e in ev
                  if any(ptr == s or ptr.startswith(s + "/") for s in e["supports"])]
        if not quotes:
            R.err(where, f"no evidence covers {ptr}")
            continue
        last = ptr.rsplit("/", 1)[-1]
        if isinstance(val, bool):
            continue
        if isinstance(val, (int, float)):
            if not any(number_in_quote(val, q) for q in quotes):
                R.err(where, f"the number {val} at {ptr} is in none of its quotes")
        elif last == "unit":
            if val in ("1",):
                continue
            words = aliases.get(val, [val.casefold()])
            if not any(w in q.casefold() for q in quotes for w in words):
                R.err(where, f"the unit {val} at {ptr} is in none of its quotes")
        elif last == "op":
            if not any(has_word(q, w) for q in quotes for w in LIMIT_WORDS.get(val, ())):
                R.err(where, f"the limit operator {val} at {ptr} is in none of its quotes")
        elif isinstance(val, str) and identifier_path(where, ptr):
            if not any(norm(val) in norm(q) for q in quotes):
                R.err(where, f"the identifier '{val}' at {ptr} is in none of its quotes")
    # Rule 6: `code` is exempt, so leaves() never yields /analyte/code; the analyte is covered here explicitly.
    if "analyte" in el:
        quotes = [e["quote"] for e in ev if "/analyte" in e["supports"] or "/analyte/code" in e["supports"]]
        code = el["analyte"]["code"]
        t = analyte_term(V, el.get("key"), code)
        if not quotes:
            R.err(where, "no evidence covers /analyte")
        elif t and not any(has_symbol(q, t["symbol"]) or any(has_alias(q, a) for a in t.get("aliases", []))
                         for q in quotes):
            R.err(where, f"the analyte {code} is in none of its quotes")


def identifier_path(where: str, ptr: str) -> bool:
    for prefix, pattern in IDENTIFIER_PATHS.items():
        if (where == prefix or where.startswith(prefix)) and pattern.fullmatch(ptr):
            return True
    return False


# ----------------------------------------------------------------- main check
def check(doc: dict, V: dict, schema: dict, sources: Path | None = None) -> tuple[Report, dict]:
    import jsonschema
    R = Report()
    info = {}
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        R.err("/" + "/".join(map(str, e.absolute_path)), "schema: " + e.message[:300])
    if R.errors:
        return R, info

    route = doc["source"]["route"]
    lang = doc["default_language"]
    if doc["vocab_version"] != V["basis"]["vocab_version"]:
        R.warn("/vocab_version", f"checked against vocabulary {V['basis']['vocab_version']}")
    if doc["dossier_id"].split(":")[0] != doc["source"]["publisher"]["domain"]:
        R.err("/dossier_id", "the domain part must equal source.publisher.domain")

    # R1 ids
    ids = {}
    def reg(i, kind, el, where):
        if i in ids:
            R.err(where, f"duplicate id '{i}'")
        ids[i] = (kind, el)
    for arr, i, el in elements(doc):
        reg(el["id"], arr, el, f"/{arr}/{i}")
        for j, s in enumerate(el.get("series", [])):
            reg(s["id"], "series", s, f"/{arr}/{i}/series/{j}")
    for i, c in enumerate(doc.get("composition", {}).get("components", [])):
        reg(c["id"], "components", c, f"/composition/components/{i}")
    media = {m["id"]: m for m in doc.get("media", [])}

    # R2 references + R8 visibility
    def ref(where, el, target, kinds):
        if target is None:
            return
        got = ids.get(target)
        if not got:
            R.err(where, f"reference '{target}' does not resolve")
        elif got[0] not in kinds:
            R.err(where, f"reference '{target}' must point to one of {kinds}, not {got[0]}")
        elif el.get("visibility", "public") == "public" and got[1].get("visibility") == "restricted":
            R.err(where, f"a public element references the restricted element '{target}'")

    def subject_refs(where, el, subj):
        if subj:
            ref(where, el, subj.get("formulation"), ("formulations",))

    for arr, i, el in elements(doc):
        w = f"/{arr}/{i}"
        if el.get("curated") is True and route not in ("extracted", "curated"):
            R.err(w, "curated: true is allowed only in extracted or curated dossiers")
        for e in el.get("evidence", []):
            ref(w, el, e["source"], ("media",))
        if arr == "properties":
            subject_refs(w, el, el["subject"])
            ref(w, el, el.get("study"), ("studies",))
            ref(w, el, el["value"].get("in_figure"), ("media",))
            ref(w, el, (el.get("comparison") or {}).get("ref"), ("formulations", "properties"))
        elif arr == "datasets":
            subject_refs(w, el, el["subject"])
            ref(w, el, el.get("study"), ("studies",))
            ref(w, el, el.get("figure"), ("media",))
            for s in el["series"]:
                subject_refs(w, el, s.get("subject"))
        elif arr == "studies":
            for a in el.get("arms", []):
                ref(w, el, a.get("formulation"), ("formulations",))
            ref(w, el, el.get("report"), ("media",))
        elif arr == "relations":
            for t in el.get("support", []):
                ref(w, el, t, ("properties", "datasets", "studies"))
        elif arr == "attestations":
            ref(w, el, el.get("document"), ("media",))
        elif arr == "statements":
            for t in el.get("supports", []):
                ref(w, el, t, ("properties", "datasets", "studies"))
    src = doc["source"]
    for t in (src.get("extraction") or src.get("curation") or {}).get("sources", []):
        if ids.get(t, ("",))[0] != "media" or media[t]["kind"] != "source_document":
            R.err("/source", f"source '{t}' is not a source_document media element")
    if "authorization" in src and src["authorization"].get("document"):
        ref("/source/authorization", {}, src["authorization"]["document"], ("media",))
    for i, c in enumerate(doc.get("composition", {}).get("components", [])):
        if "refines" in c:
            t = ids.get(c["refines"])
            if not t or t[0] != "components":
                R.err(f"/composition/components/{i}", "refines must name a component")
            elif c.get("visibility") != "restricted" or t[1].get("visibility") == "restricted":
                R.err(f"/composition/components/{i}", "refines: a restricted component refines a public one")

    # R7 languages
    def walk_text(node, where):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("text", "label", "title", "caption", "name") and isinstance(v, dict) and v \
                        and all(isinstance(x, str) for x in v.values()) and lang not in v:
                    R.err(f"{where}/{k}", f"no entry for the default language '{lang}'")
                walk_text(v, f"{where}/{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk_text(v, f"{where}/{i}")
    walk_text({k: doc[k] for k in ARRAYS if k in doc}, "")

    # R3 vocabulary + R4 values
    def vocab(where, name, key):
        if is_x(key):
            R.warn(where, f"extension key {key}: stored, not interpreted")
        elif not in_vocab(V, name, key):
            R.err(where, f"'{key}' is not in vocabulary {name}")
        elif V[name]["_keys"][key].get("deprecated"):
            R.warn(where, f"'{key}' is deprecated in vocabulary {name}")

    def check_conditions(where, conds):
        for c in conds:
            k = c["key"]
            if is_x(k):
                R.warn(where, f"extension key {k}: stored, not interpreted")
                continue
            t = V["condition-keys"]["_keys"].get(k)
            if not t:
                R.err(where, f"'{k}' is not in vocabulary condition-keys")
                continue
            d = unit_dim(V, t.get("dimension"))
            if "value" in c and d and c["unit"] not in d["units"]:
                R.err(where, f"condition {k}: unit {c['unit']} is not accepted for {d['key']}")
            if k == "sensory_attribute" and "code" in c:
                vocab(where, "sensory", c["code"])
            if k == "endpoint" and "code" in c:
                vocab(where, "endpoints", c["code"])

    def check_method(where, m):
        if not m:
            return
        if "standard" in m:
            body = m["standard"].split(":")[0]
            if body not in {b["key"] for b in V["test-methods"]["bodies"]}:
                R.err(where, f"method.standard: unknown body '{body}'")
        check_conditions(where, m.get("settings", []))

    def check_scope(where, sc):
        for pt in (sc or {}).get("product_type", []):
            vocab(where, "product-types", pt)

    for i, p in enumerate(doc.get("properties", [])):
        w = f"/properties/{i}({p['id']})"
        key, val = p["key"], p["value"]
        check_conditions(w, p.get("conditions", []))
        check_method(w, p.get("method"))
        check_scope(w, p.get("scope"))
        if is_x(key):
            R.warn(w, f"extension key {key}: stored, not interpreted")
            continue
        t = key_term(V, key)
        if not t:
            R.err(w, f"'{key}' is not in vocabulary property-keys")
            continue
        an = t.get("analyte")
        if an and "analyte" not in p:
            R.err(w, f"{key} needs analyte")
        elif "analyte" in p and not an:
            R.err(w, f"analyte is not allowed for {key}")
        elif an:
            c = p["analyte"]["code"]
            if is_x(c):
                R.warn(w, f"extension analyte '{c}' is not projected")
            elif c not in V.get(an, {}).get("_keys", {}):
                R.err(w, f"analyte code '{c}' not in vocabulary {an}")
        if an:
            if p["subject"]["kind"] != "neat":
                R.err(w, f"{key} is stated for the material as supplied (subject neat)")
            if p["basis"] not in ANALYTE_BASES:
                R.err(w, f"basis {p['basis']} is not allowed for {key}")
            if p.get("scope") or p.get("conditions"):  # an empty list counts as absent
                R.err(w, f"{key} takes no scope or conditions")
        form = next(iter(val))
        if form not in t["forms"]:
            R.err(w, f"value form '{form}' is not allowed for {key} (allowed: {', '.join(t['forms'])})")
        if form == "nominal" and not is_x(val["nominal"]):
            if not nominal_ok(V, t.get("nominal_set", ""), val["nominal"]):
                R.err(w, f"nominal code '{val['nominal']}' is not in set {t.get('nominal_set')}")
        if form == "text" and lang not in val["text"]:
            R.err(w, f"value.text has no entry for the default language '{lang}'")
        if form == "range" and val["range"]["min"] > val["range"]["max"]:
            R.err(w, "range.min is above range.max")
        if form in NUMERIC_FORMS:
            d = unit_dim(V, t.get("dimension"))
            factor = 1
            if d:
                if p["unit"] not in d["units"]:
                    R.err(w, f"unit {p['unit']} is not accepted for {key} (dimension {d['key']}: {', '.join(d['units'])})")
                    continue
                factor = d["units"][p["unit"]]
            if factor is not None:
                for n in numbers_of(val):
                    c = n * factor
                    if "min" in t and c < t["min"] or "max" in t and c > t["max"]:
                        R.err(w, f"value {n} {p['unit']} is outside the plausible range of {key} "
                                 f"[{t.get('min', '-inf')}, {t.get('max', 'inf')}]")
        if p["basis"] == "regulatory_limit" and len(p["as_of"]) < 4:
            R.err(w, "a regulatory limit needs as_of")

    for i, d in enumerate(doc.get("datasets", [])):
        w = f"/datasets/{i}({d['id']})"
        check_method(w, d.get("method"))
        check_conditions(w, d.get("conditions", []))
        for a in d["axes"]:
            k = a["key"]
            if is_x(k):
                continue
            t = key_term(V, k) if "." in k else V["condition-keys"]["_keys"].get(k)
            if not t:
                R.err(w, f"axis key '{k}' is neither a property key nor a condition key")
                continue
            dim = unit_dim(V, t.get("dimension"))
            if a["type"] == "numeric" and dim and a["unit"] not in dim["units"]:
                R.err(w, f"axis {k}: unit {a['unit']} is not accepted for {dim['key']}")
        for s in d["series"]:
            check_conditions(w, s.get("conditions", []))
            for pt in s.get("points", []):
                if len(pt) != len(d["axes"]):
                    R.err(w, f"series {s['id']}: a point has {len(pt)} values for {len(d['axes'])} axes")
                    break
                for a, x in zip(d["axes"], pt):
                    if a["type"] == "numeric" and not isinstance(x, (int, float)):
                        R.err(w, f"series {s['id']}: non-numeric value on numeric axis {a['key']}")
                    if a["type"] != "numeric" and x not in {l["code"] for l in a["legend"]}:
                        R.err(w, f"series {s['id']}: '{x}' is not in the legend of axis {a['key']}")

    for i, f in enumerate(doc.get("formulations", [])):
        w = f"/formulations/{i}({f['id']})"
        for k, name in (("product_type", "product-types"), ("product_form", "product-forms")):
            if k in f:
                vocab(w, name, f[k])
        for ln in f["lines"]:
            if "function" in ln:
                vocab(w, "functions", ln["function"])
        total = sum(ln.get("percent", 0) for ln in f["lines"])
        qs = sum(1 for ln in f["lines"] if ln.get("qs"))
        if qs > 1:
            R.err(w, "more than one q.s. line")
        if f["disclosure"] == "full":
            if qs == 0 and abs(total - 100) > 0.5:
                R.err(w, f"a fully disclosed formulation must add up to 100 % (is {total:g})")
            if qs == 1 and total >= 100:
                R.err(w, f"the lines beside the q.s. line add up to {total:g} %")
        elif total > 100.5:
            R.err(w, f"the lines add up to {total:g} %")

    for i, s in enumerate(doc.get("studies", [])):
        vocab(f"/studies/{i}", "study-kinds", s["kind"])
        check_method(f"/studies/{i}", s.get("method"))
        check_conditions(f"/studies/{i}", s.get("application", []))
    for i, r in enumerate(doc.get("relations", [])):
        vocab(f"/relations/{i}", "interaction-effects", r["effect"])
        if "class" in r["with"]:
            vocab(f"/relations/{i}", "interaction-classes", r["with"]["class"])
        check_conditions(f"/relations/{i}", r.get("conditions", []))
    for i, a in enumerate(doc.get("attestations", [])):
        w = f"/attestations/{i}({a['id']})"
        vocab(w, "attestation-schemes", a["scheme"])
        vocab(w, "attestation-statuses", a["status"])
        check_scope(w, a.get("scope"))
        for c in (a.get("usage_restriction") or {}).get("codes", []):
            vocab(w, "usage-restrictions", c)
        if a.get("valid_from") and a.get("valid_until") and a["valid_from"] > a["valid_until"]:
            R.err(w, "valid_from is after valid_until")
        if a["status"] == "certified" and not (a.get("issuer") and a.get("valid_until")):
            R.err(w, "a certified attestation needs issuer and valid_until")
        if a["scheme"] == "ifra" and not (a.get("edition") and a.get("limits")):
            R.err(w, "an IFRA attestation needs edition and limits")
    for i, s in enumerate(doc.get("statements", [])):
        w = f"/statements/{i}({s['id']})"
        vocab(w, "statement-kinds", s["kind"])
        check_scope(w, s.get("scope"))
        if s["kind"] in ("guidance", "checklist") and any(len(t) > 300 for t in s["text"].values()):
            R.err(w, "guidance and checklist lines are limited to 300 characters")
    for i, m in enumerate(doc.get("media", [])):
        if "document" in m:
            vocab(f"/media/{i}", "document-kinds", m["document"]["kind"])
        if route in ("manufacturer", "distributor") and m.get("visibility", "public") == "public" \
                and m["kind"] != "source_document" and m["license"]["redistribution"] == "none":
            R.err(f"/media/{i}", "public media of a publisher need redistribution 'allowed' or 'consumer_display'")

    # R5 composition
    comp = doc.get("composition")
    if comp:
        refined = {c["refines"] for c in comp["components"] if "refines" in c}
        lo = hi = 0.0
        for i, c in enumerate(comp["components"]):
            w = f"/composition/components/{i}"
            vocab(w, "composition-roles", c["role"])
            if "origin" in c:
                vocab(w, "origin-types", c["origin"]["type"])
            if c["id"] in refined:
                continue
            v = c.get("content")
            if v is None or "nominal" in v:
                hi += 0 if v else 100
                continue
            if "exact" in v:
                lo, hi = lo + v["exact"], hi + v["exact"]
            elif "range" in v:
                if v["range"]["min"] > v["range"]["max"]:
                    R.err(w, "range.min is above range.max")
                lo, hi = lo + v["range"]["min"], hi + v["range"]["max"]
            elif v["limit"]["op"] in ("<", "<="):
                hi += v["limit"]["value"]
            else:
                lo, hi = lo + v["limit"]["value"], hi + 100
        if lo > 100 + 1e-9:
            R.err("/composition", f"the minimum contents add up to {lo:g} %")
        if comp["complete"] and hi < 100 - 1e-9:
            R.err("/composition", f"complete is true but the maximum contents add up to only {hi:g} %")

    # R10 view rules
    forms = {f["id"]: f for f in doc.get("formulations", [])}
    studies = {s["id"]: s for s in doc.get("studies", [])}

    def subject_line(fid):
        return next((ln for ln in forms.get(fid, {}).get("lines", [])
                     if ln.get("is_subject") and "percent" in ln), None)

    def has_method(p):
        m = p.get("method") or {}
        return "standard" in m or m.get("non_standard") is True

    for i, p in enumerate(doc.get("properties", [])):
        w = f"/properties/{i}({p['id']})"
        key, subj = p["key"], p["subject"]
        t = key_term(V, key) if not is_x(key) else None
        views = (t or {}).get("views", [])
        conds = {c["key"]: c for c in conditions_of(p)}
        if "uv_performance" in views:
            f = forms.get(subj.get("formulation"))
            if subj["kind"] != "formulation" or not f:
                R.err(w, "uv_performance: the result must be tied to a test formulation")
            else:
                if f["disclosure"] == "partial":
                    R.err(w, "uv_performance: the formulation must disclose every UV filter and booster with its %")
                if f["role"] in ("starting_formula", "test_formula") and not subject_line(f["id"]):
                    R.err(w, "uv_performance: the formulation has no line for this material (is_subject + percent)")
            if not has_method(p):
                R.err(w, "uv_performance: method.standard (or non_standard: true) is required")
            if key == "uv.spf_boost" and (p.get("comparison") or {}).get("ref") not in forms:
                R.err(w, "uv.spf_boost: comparison.ref must name the comparator formulation")
            if key == "uv.spf_calculated" and p["basis"] != "calculated":
                R.err(w, "uv.spf_calculated: basis must be calculated")
        if "efficacy" in views:
            st = studies.get(p.get("study"))
            if not st:
                R.err(w, "efficacy: study is required")
            if subj["kind"] == "neat" and "material_conc" not in subj:
                pass
            elif "material_conc" not in subj and not subject_line(subj.get("formulation")):
                R.err(w, "efficacy: the concentration of the material in the tested system is required")
            for req in ("comparison", "statistics", "outcome"):
                if req not in p:
                    R.err(w, f"efficacy: {req} is required")
            if key == "consumer.agreement" and st and st["kind"] != "consumer_perception":
                R.err(w, "consumer.agreement belongs to a consumer_perception study")
            if key.startswith("efficacy.") and st and st["kind"] == "consumer_perception":
                R.err(w, "a consumer_perception study reports consumer.agreement, not efficacy.*")
        if "rheology" in views and next(iter(p["value"])) in NUMERIC_FORMS + ("in_figure",) and key != "rheology.viscosity_change":
            if "temperature" not in conds:
                R.err(w, "rheology: the temperature condition is required")
            if key == "rheology.viscosity" and subj["kind"] in ("dilution", "formulation") \
                    and not ({"shear_rate", "rotation_speed"} & set(conds)):
                R.err(w, "rheology: shear_rate or rotation_speed is required")
        if key == "micro.mic":
            o = conds.get("organism")
            if not o or "ref_id" not in o:
                R.err(w, "preservation: the organism condition with its strain number (ref_id) is required")
        if key.startswith("micro.challenge") and subj["kind"] != "formulation":
            R.err(w, "preservation: a challenge test result must be tied to the tested formulation")
        if "safety" in views:
            if not has_method(p):
                R.err(w, "safety: method.standard (or non_standard: true) is required")
            if subj["kind"] not in ("neat", "reference_material") and "material_conc" not in subj:
                R.err(w, "safety: the test concentration is required")
        if key.startswith("origin.") and "index" in key and not has_method(p):
            R.err(w, "sustainability: method.standard is required for an ISO 16128 index")
        if key.startswith("eco.biodegrad") and not has_method(p):
            R.err(w, "sustainability: method.standard is required")
    for i, d in enumerate(doc.get("datasets", [])):
        keys = {a["key"] for a in d["axes"]}
        if "rheology.viscosity" in keys:
            for s in d["series"]:
                have = keys | {c["key"] for c in conditions_of(d, s)}
                if "temperature" not in have or not ({"shear_rate", "rotation_speed"} & have):
                    R.err(f"/datasets/{i}({d['id']})", f"rheology: series {s['id']} needs temperature and shear_rate or rotation_speed")

    view, missing = usage_view(doc, V)
    general_levels = [p for p in doc.get("properties", []) if p["key"] == "use.level" and p["basis"] == "recommended"
                      and p["subject"]["kind"] == "neat" and "scope" not in p and not p.get("conditions")]
    if len(general_levels) > 1:
        R.err("/properties", "usage: more than one general recommended use.level (scope the others)")
    u = view.get("usage", {})
    if u:
        lo = u.get("min", 0)
        if not (0 < u["max"] <= 100 and 0 <= lo <= u["max"]):
            R.err("/properties", "usage: use.level must satisfy 0 <= min <= max, 0 < max <= 100")
        if "typical" in u and not lo <= u["typical"] <= u["max"]:
            R.err("/properties", "usage: use.level_typical must lie inside the use.level range")
    for kind in ("guidance", "checklist"):
        n = sum(1 for s in doc.get("statements", []) if s["kind"] == kind and "scope" not in s)
        if n > 6:
            R.warn("/statements", f"usage: {n} general {kind} lines; the usage view keeps the first six")
    info["usage_view"], info["usage_view_missing"] = view, missing

    # R11 evidence
    if route == "extracted":
        if doc["identity"].get("curated") is not True:
            check_evidence("/identity", doc["identity"], V, media, sources, R)
        for i, c in enumerate(doc.get("composition", {}).get("components", [])):
            check_evidence(f"/composition/components/{i}", c, V, media, sources, R)
        for arr, i, el in elements(doc):
            if arr == "media":
                continue
            check_evidence(f"/{arr}/{i}({el['id']})", el, V, media, sources, R)
        for i, d in enumerate(doc.get("datasets", [])):
            if d["points_origin"] == "publisher_raw":
                R.err(f"/datasets/{i}", "an extracted dossier has no publisher_raw points")

    # R12 conformance level
    level, why = conformance(doc, V, missing)
    info["computed_level"], info["level_gaps"] = level, why
    claimed = doc["conformance_level"]
    if level is None:
        R.err("/conformance_level", "below L1: " + "; ".join(why["L1"]))
    elif claimed > level:
        nxt = f"L{int(level[1]) + 1}"
        R.err("/conformance_level", f"claims {claimed} but reaches {level}: " + "; ".join(why[nxt]))
    return R, info


def conformance(doc, V, usage_missing):
    props = doc.get("properties", [])
    why = {"L1": list(usage_missing), "L2": [], "L3": []}
    keys = {p["key"] for p in props}
    comp = doc.get("composition")
    if not comp:
        why["L2"].append("no composition")
    elif any("content" not in c for c in comp["components"]):
        why["L2"].append("a component has no content")
    for k in ("profile.function", "profile.physical_form"):
        if k not in keys:
            why["L2"].append(f"no {k}")
    if sum(1 for p in props if p["basis"] in ("specification", "typical")) < 3:
        why["L2"].append("fewer than three specification or typical properties")
    if not ({"stability.shelf_life", "stability.retest_period"} & keys):
        why["L2"].append("no shelf life or retest period")
    groups = {V["attestation-schemes"]["_keys"].get(a["scheme"], {}).get("group") for a in doc.get("attestations", [])}
    if "regulatory" not in groups:
        why["L2"].append("no regulatory status attestation")
    if not any(m.get("document", {}).get("kind") == "sds" for m in doc.get("media", [])):
        why["L2"].append("the SDS is not referenced as a source document")
    if any("in_figure" in p["value"] for p in props):
        why["L3"].append("a value exists only in a figure")
    if any(d["points_origin"] == "none" for d in doc.get("datasets", [])):
        why["L3"].append("a dataset has a figure but no numeric series")
    used = {p.get("study") for p in props} | {d.get("study") for d in doc.get("datasets", [])}
    for s in doc.get("studies", []):
        if s.get("all_endpoints_reported") is not True:
            why["L3"].append(f"study {s['id']}: all_endpoints_reported is not true")
        if s["id"] not in used:
            why["L3"].append(f"study {s['id']} has no structured result")
        if s["kind"] in ("in_vivo", "consumer_perception", "sensory_panel") and "subjects" not in s:
            why["L3"].append(f"study {s['id']}: subjects.n is missing")
        if "lab" not in s:
            why["L3"].append(f"study {s['id']}: lab is missing")
    if any((p.get("statistics") or {}).get("significant") == "not_reported" for p in props
           if "efficacy" in (key_term(V, p["key"]) or {}).get("views", [])):
        why["L3"].append("a result does not report significance")
    if (doc.get("declarations") or {}).get("negative_results_included") is not True:
        why["L3"].append("declarations.negative_results_included is not true")
    if doc["completeness"] != "full":
        why["L3"].append("completeness is not full")
    if why["L1"]:
        return None, why
    if why["L2"]:
        return "L1", why
    if why["L3"]:
        return "L2", why
    return "L3", why


# ----------------------------------------------------------------- precedence (SPEC 8)
def may_replace(active: dict, candidate: dict) -> tuple[bool, str]:
    """Whether `candidate` replaces `active` for the same material (SPEC 8.2)."""
    ra, rc = RANK[active["source"]["route"]], RANK[candidate["source"]["route"]]
    if rc > ra:
        return True, "stronger source"
    if rc < ra:
        return False, "weaker source never replaces a stronger one"
    if active["source"]["publisher"]["domain"] != candidate["source"]["publisher"]["domain"]:
        return False, "same rank, different publisher: needs a decision by the consumer"
    if candidate["dossier_id"] != active["dossier_id"]:
        return False, "same publisher, different dossier_id: needs a decision by the consumer"
    if candidate["version"] > active["version"]:
        return True, "newer version of the same dossier"
    return False, "not a newer version"


# ----------------------------------------------------------------- index
def check_index(path: Path, schema: dict) -> Report:
    import jsonschema
    R = Report()
    idx = json.loads(path.read_text(encoding="utf-8"))
    for e in jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).iter_errors(idx):
        R.err("/" + "/".join(map(str, e.absolute_path)), "schema: " + e.message[:300])
    if R.errors:
        return R
    hosts = {idx["publisher"]["domain"], *idx.get("hosts", [])}
    seen = set()
    for i, d in enumerate(idx["dossiers"]):
        w = f"/dossiers/{i}({d['dossier_id']})"
        if d["dossier_id"] in seen:
            R.err(w, "listed twice")
        seen.add(d["dossier_id"])
        if d["dossier_id"].split(":")[0] != idx["publisher"]["domain"]:
            R.err(w, "dossier_id is not under the publisher's domain")
        for rep in ("public", "restricted"):
            if rep not in d:
                continue
            host = d[rep]["url"].split("/")[2]
            if not any(host == h or host.endswith("." + h) for h in hosts):
                R.err(w, f"{rep}.url is served from {host}, which is neither the publisher's domain nor in hosts")
            local = path.parent / d[rep]["url"].rsplit("/", 1)[-1]
            if local.exists():
                raw = local.read_bytes()
                if "sha256:" + hashlib.sha256(raw).hexdigest() != d[rep]["hash"]:
                    R.err(w, f"{rep}.hash does not match {local.name}")
                doc = json.loads(raw)
                for k in ("dossier_id", "version", "conformance_level", "standard_version", "vocab_version"):
                    if doc.get(k) != d.get(k):
                        R.err(w, f"{k} differs between the index and {local.name}")
                if doc["representation"] != rep or doc["source"]["route"] != d["route"]:
                    R.err(w, f"{local.name}: representation or route differs from the index")
            else:
                R.warn(w, f"{local.name} is not next to the index; hash not checked")
    return R


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--vocab", type=Path, default=ROOT / "vocab")
    ap.add_argument("--schema", type=Path, default=ROOT / "schema")
    ap.add_argument("--sources", type=Path)
    ap.add_argument("--usage-view", action="store_true")
    ap.add_argument("--index", type=Path)
    a = ap.parse_args(argv)
    if not a.files and not a.index:
        ap.print_usage()
        return 2
    V = load_vocab(a.vocab)
    bad = 0
    if a.index:
        R = check_index(a.index, json.loads((a.schema / "index.schema.json").read_text()))
        print(f"{'FAIL' if R.errors else 'OK  '} {a.index.name}  index")
        for m in R.errors:
            print("   error  ", m)
        for m in R.warnings:
            print("   warning", m)
        bad += bool(R.errors)
    schema = json.loads((a.schema / "dossier.schema.json").read_text())
    for f in a.files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        if a.usage_view:
            view, missing = usage_view(doc, V)
            print(json.dumps({"usage_view": view, "missing": missing}, indent=2, ensure_ascii=False))
            continue
        R, info = check(doc, V, schema, a.sources)
        counts = " ".join(f"{k}={len(doc.get(k, []))}" for k in ARRAYS if doc.get(k))
        print(f"{'FAIL' if R.errors else 'OK  '} {f.name}  route={doc.get('source', {}).get('route')} "
              f"claimed={doc.get('conformance_level')} computed={info.get('computed_level')}  {counts}")
        for m in R.errors:
            print("   error  ", m)
        for m in R.warnings:
            print("   warning", m)
        bad += bool(R.errors)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
