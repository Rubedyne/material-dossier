# Design notes — Rubedyne Material Dossier 1.0

Date: 2026-11-14, updated 2026-11-23. Status: 1.0, public draft 5 for feedback (tag v1.0.0-draft.5).

These notes are not normative. They record why the standard looks the way it does, what was rejected, how
Rubedyne's v1 material playbook maps onto it, what is still open, and how the files were verified.

## 1. Inputs and how the design was tested

- A concept review (2026-11-14) of a corpus of supplier documents (not published): an inventory of the corpus,
  the nine-primitive proposal, 29 real data points mapped onto it, risks and 13 ranked recommendations. It is the
  main input and was adopted in structure.
- The v1 material playbook and its validator, and the curator workflow. The v1 material playbook is the
  per-material usage record of Rubedyne's formulation software: a YAML file with use level, phase, pH window,
  maximum temperature, guidance and checklist lines.
- Two owner decisions that arrived during the work: the name (**Material Dossier**, not "Material Runbook"), and
  the merge of the v1 material playbook into the dossier as its usage view, with a minimal L1 dossier and a
  `curated` source.
- A small sample of the corpus: the first two pages of five documents (one TDS, one specification,
  one presentation, one allergen statement, one portfolio leaflet). The review's 29 data points were not re-checked.
  The sample led to three additions: `content.nominal` (`not_detected`) for allergen tables with "n.d.";
  `profile.application` for "used in conditioners and shampoos"; the `size_distribution_basis` condition for
  number- versus volume-weighted particle sizes.
- **Not checked:** scanned documents, non-PDF files, and everything the review lists as unchecked. Nothing from the
  corpus appears in these files; every example is invented.

## 2. Review recommendations: adopted, changed

| # | Review recommendation | Outcome |
|---|---|---|
| 1 | Primitives + vocabularies + views | Adopted. Nine primitives, 24 vocabulary files, 13 views. |
| 2 | `property` core: mandatory `basis`, `subject`, closed `value` union | Adopted unchanged in substance. |
| 3 | No publisher free text in generate prompts | Adopted as a consumer rule (SPEC 14.2), with one exception introduced by the usage-view decision: lines a person at the consumer approved. See open issue 1. |
| 4 | Plausibility and cross-checks on the publisher route, semantic diff | Plausibility bounds are in `vocab/property-keys.json` and are part of validation (SPEC 11.2). Cross-checks against the consumer's own data and the diff are consumer behaviour (SPEC 14.1, SHOULD); stable element ids make the diff possible. |
| 5 | `evidence[]` with field-level assignment | Adopted (SPEC 7.3): `supports` are JSON Pointers; checks for quote, number, unit, limit operator, thousands separators. The measurement on a hand-checked sample of real documents that the review asks for is still to be done (open issue 12). |
| 6 | Mandatory test formulation for UV results | Adopted as a view rule (SPEC 6.6) and a consumer rule (SPEC 14.3). How a consumer enforces the ban is implementation, not standard. |
| 7 | `standard_version`, `vocab_version`, `x-<domain>:` keys | Adopted (SPEC 13). |
| 8 | `as_of` everywhere, `valid_until` on certificates | Adopted; `as_of` is required on every element by the schema. |
| 9 | Conformance levels with numeric series at L3 | Adopted; the content of L1 changed (below). |
| 10 | Endpoint: domain binding, hash, increasing version, own copies of images, room for a signature | Adopted (SPEC 9, 5.12, 15). |
| 11 | External vocabularies | Adopted: UCUM, CosIng, ISO/OECD/Ph. Eur. designations, ISO 3166, BCP 47, SPDX. |
| 12 | Extraction deny-list (market percentages, batch data, "no data" rows, other makers' data) | Not part of the standard; it belongs to the extraction prompt. The standard states the consequences: batch data and market surveys are out of scope, unknown values are left out, other materials are `reference_material`. |
| 13 | Storage: whole dossier per version plus a flattened property index | Consumer guidance only (SPEC 14.1). |

Where the result differs from the review's sketch:

| Review | Standard | Why |
|---|---|---|
| `identity` holds the header (versions, publisher) | Envelope and `source` are separate from `identity` | Versioning and precedence concern the document; identity concerns the material. Precedence compares `source` and `identity` separately. |
| `identity.variant`, `applies_to` on every element | `identity.grade`; no `applies_to` | Owner decision: one dossier = one sellable grade. A member that lets one dossier describe several forms would contradict it. |
| View `playbook_core` with `stability.ph_window`, `process.max_temperature` | View `usage` with `use.ph_window`, `use.process_temperature_max`; `stability.ph_range` is a different key | The pH in which a material is stable and the pH window recommended for the formulation are different facts (review data point 26 has both). The usage view takes the recommendation. |
| `nominal: {code}` | `nominal: "<code>"` | One member less; nothing else ever sat next to `code`. |
| `significant: true / false / not_reported` | `"yes" / "no" / "not_reported"` | No mixed boolean/string type. |
| `provenance {route, evidence}` on each property | `source.route` once per dossier; `evidence[]` and `curated` per element | A dossier has one route (precedence works on it). The only per-element exception needed is a curator-written line inside an extracted dossier. |
| `spec.*` keys | No such namespace; `basis: specification` | The key names the property. Otherwise every key would exist twice. |
| `efficacy.hydration` as plain keys | Pattern `efficacy.<endpoint>` with the suffix from `endpoints.json` | Keeps one endpoint vocabulary for studies, conditions and searches. |
| `method.standard` free ("ISO 24444") | `<body>:<designation>`, closed list of bodies, open designations, a registry of well-known methods | A fully closed method list cannot be complete; a free string cannot be matched. |
| Canonical unit only | Canonical unit plus accepted units with exact factors | An extracted dossier must keep the source's number, or the number check fails. Consumers convert. |
| `dataset.value_type` | `type` per axis (`numeric`, `ordinal`, `category`) | A challenge-test matrix has category axes (organism) and an ordinal result in one dataset. |
| L1 = identity + composition + playbook core | L1 = identity + complete usage view; composition moves to L2 | Owner decision on the minimal L1 dossier ("only identity + the usage view"). |
| `media.sha256` with files served from the consumer's storage | Same; additionally `license.redistribution` | The review's copyright concern needs a machine-readable answer to "may a consumer show this to its users". |

## 3. Decisions and rejected alternatives

1. **JSON, one document per dossier.** YAML (as in the v1 playbook) was rejected for the standard: comments and
   multiple spellings of the same value make hashing and validation weaker, and JSON Schema tooling is universal.
2. **Closed structure, vocabulary membership outside the schema.** The schema validates shapes and structural
   enumerations; vocabulary keys are only pattern-checked there and resolved against `vocab/` in a second step.
   Rejected: enumerating all vocabulary keys in the schema. That would couple `standard_version` to
   `vocab_version`, which the owner wants separate. `basis` is the one vocabulary mirrored in the schema, because
   schema conditionals depend on it; the verification asserts both lists are equal.
3. **Typed lists per topic (`studies[]` with result fields, `uv_results[]`, `mic_table[]`) rejected** in favour of
   properties plus views, as the review argues: each topic list would re-implement ranges, limits, units, methods
   and statistics.
4. **Pure key–value model rejected**: without mandatory `basis` and `subject` and without view rules, SQL matching
   for substitution and the UV rule cannot be enforced.
5. **Functions, form and sensory descriptors are properties with nominal values**, not arrays on `identity`. It is
   more verbose for publishers (about six lines per function) but keeps one mechanism for evidence, `as_of`,
   visibility and indexing. The publisher guide shows the pattern.
6. **`as_of` required on every element**, not inherited from a dossier-level default. A default would be filled
   with today's date and defeat the data-age rule. Reduced precision (`2024`, `2024-02`) keeps it cheap.
7. **Content hash over the exact octets** (SPEC 9.4). Rejected: a hash over canonical JSON (RFC 8785). It would
   survive re-serialisation, but needs a canonicalisation library on the publisher's side and has number-format
   pitfalls; a manufacturer can compute an octet hash with `sha256sum` on a static file.
8. **Two representations per version** (public, restricted) instead of field-level encryption or stub elements in
   the public document. The public representation stays a complete, self-consistent dossier; `restricted_content`
   announces that more exists. The price: a public element cannot point to a restricted one (a public study cannot
   link its restricted report; example 01 solves it with a restricted statement).
9. **Index at a fixed well-known URL** as the domain binding. Rejected for 1.0: DNS TXT records (harder for a
   manufacturer's web team, no gain when HTTPS already proves control) and a central registry (the standard should
   work without Rubedyne operating anything).
10. **Signature optional**, as a detached JWS over the same octets. The hash and the human-approved domain pairing
    carry 1.0; the members are reserved so that 1.1 can require it.
11. **Raster images and PDF only.** SVG was rejected for the reason the review gives (active content).
12. **Replacement, not merge.** One dossier per material means a stronger dossier replaces a weaker one whole.
    Merging elements from several sources into one document was rejected: provenance per element would return,
    and "who answers for this dossier" would have no answer.
13. **A reference checker ships in the repository** (`tools/check_dossier.py`). The rules of SPEC 11.2–11.4 and
    section 12 are not expressible in JSON Schema; without a runnable form they would be untested prose, and the
    validation log below would not be reproducible. It is marked non-normative.

## 4. Owner decisions and where they landed

| Decision | Where |
|---|---|
| One dossier = one sellable grade; family optional | SPEC 5.3 |
| One dossier per material; ranking; manufacturer only replaced by newer manufacturer | SPEC 8 |
| Source recorded | `source.route` (SPEC 5.2) |
| Publisher routes: structural validation only; extracted: field-level evidence; no "dropped" list | SPEC 7 |
| Versioned dossiers, hash; `standard_version`, `vocab_version`; 1.x only adds; `x-<domain>:` | SPEC 9.4, 13 |
| Public and restricted content; minimal endpoint protocol; images by URL with hash and licence | SPEC 9, 10, 5.12 |
| Graphs as series plus figure; figure without data marked; extracted never from an image | SPEC 5.6, 7.3 |
| Sunscreen results tied to the test formulation; no product claims | SPEC 6.6, 14.3 |
| Free text display-only; `as_of`; `valid_until`; usage restrictions | SPEC 4.5, 14.2, 4.4, 5.10 |
| L1–L3 | SPEC 12 |
| External vocabularies | SPEC 13.3 |
| Coverage of the whole brochure/TDS | SPEC 5 and 6; publisher guide section 3 |
| Licences, name | `LICENSE.md` |
| Name "Material Dossier"; `dossier_id`; `$id` under `material-dossier/1.0/` | everywhere |
| Material playbook merged: usage view, minimal L1, `curated` | SPEC 6.1, 5.2, 8.2; sections 5–7 below |

## 5. The usage view is the former material playbook

The v1 material playbook no longer exists as a separate object. Its content is the **usage view** of the dossier,
defined normatively in SPEC 6.1 and implemented in `usage_view()` of the checker. Prompts and the dose / phase /
pH / temperature checks read the projection, which has exactly the v1 shape.

| v1 playbook | Dossier element | Projection rule |
|---|---|---|
| `usage.min`, `usage.max` | property `use.level`, basis `recommended`, subject `neat`, no scope, no conditions | `range` → min and max; `limit <=` → max only; `exact` → min = max |
| `usage.typical` | property `use.level_typical` (`exact`) | value |
| `phase: [A–E]` | one property `use.phase` per stage, nominal code from `process-stages` | `usage_view_phase` of the term; A = `water_phase`, B = `oil_phase`, C = `cool_down`, D = `hot_water_phase_addition`, E = `hot_oil_phase_addition`; document order, unique |
| `ph_window.min`, `.max` | property `use.ph_window` | `range` → both; `limit >=` → min; `limit <=` → max |
| `temperature.max` | property `use.process_temperature_max` | `exact` or `limit <=` → max |
| `guidance[]` (≤ 6, ≤ 300 chars) | statements of kind `guidance` without scope | first six in document order, default language, whitespace collapsed |
| `checklist[]` (≤ 6, ≤ 300 chars) | statements of kind `checklist` without scope | the same |

Properties of the mapping:

- **Lossless for v1.** Every valid v1 playbook can be written as dossier elements whose usage view equals the
  normalised playbook (verified on 2026-11-14 with the migrated example and four edge variants; see section 9).
- **The dossier can say more.** Use levels per product type or region, a regulatory maximum, stages without a
  letter (`cold_process`, `pre_dispersion`, …) are valid elements and simply not projected.
- **The view's own limits equal those of the v1 playbook validator** (0 < max ≤ 100, typical inside the range,
  pH 0–14, temperature ≤ 150, six lines, 300 characters), as vocabulary bounds and view rules; on 2026-11-14 the
  usage views of the six examples that existed then passed the v1 playbook validator (section 9).
- The v1 playbook validator stays the validator of the projection for now. When the dossier replaces the YAML in
  storage, the checker's `usage_view()` (or a port of it) becomes the single producer and the v1 playbook
  validator its consumer-side guard.

## 6. One-time migration of approved v1 playbooks

Scope: every approved v1 playbook whose material has no dossier yet. Drafts are not migrated.

| Dossier member | Value |
|---|---|
| `dossier_id` | `rubedyne.com:<lower-case slug>` |
| `version` | 1 |
| `issued` | the playbook's approval time |
| `representation`, `completeness`, `conformance_level` | `public`, `partial`, `L1` |
| `source.route` | `curated` |
| `source.publisher` | Rubedyne (`rubedyne.com`) |
| `source.curation` | `method: "migrated_playbook_v1"`, `completed`: approval date, `reference`: the playbook's id and status, `sources`: the source document when the playbook has one |
| `identity` | from the material record: its display name, manufacturer name, INCI list; `product_code` when known; `curated: true`; `as_of`: approval date |
| properties, statements | by the table in section 5; ids are fixed (`use-level`, `use-typical`, `use-phase-b`, `use-ph`, `use-temp`, `s-guidance-1`, …) so that later versions diff cleanly |
| `as_of` of the elements | the approval date (the playbook stores no document date) |
| `media` | the playbook's source document as a `source_document` (hash of the stored file, licence `unknown` / `none`) |

Value rules: `usage` with `min` → `range`; without → `limit <=`. `ph_window` with both ends → `range`; with one →
`limit`. `temperature.max` → `limit <=`. Phase letters map by the fixed table. An empty `ph_window: {}` or
`temperature: {}` is dropped.

**Evidence comments.** The v1 extractor wrote each verified quote as a trailing YAML comment,
`# "<quote>" (p.<page>)`. The migration turns such a comment into an `evidence` entry on the element
(`source`: the document, `page`, `quote`, `supports`: `/value` and `/unit`, or `/text` for lines) when the
playbook has a source document and the comment has a page. Otherwise the quote is kept in the element's `note`.
Comments that do not have this form (hand-written remarks) are not carried over and are listed in the migration
report.

**Why `curated` and not `extracted`.** The playbook was approved by a person and may have been edited by hand; its
quotes were verified when extracted, but the page text was not stored, so the evidence cannot be re-verified
element by element. A curated dossier makes no evidence promise, so the migration never claims more than is known.
Where the document is still available, a later extraction run produces a real `extracted` dossier, which then
replaces the curated one by rule 8.2.

Not migrated into the dossier: who approved the playbook, which model extracted it, and edit timestamps. They are
personal or operational data.

`examples/05-minimal-l1-curated.json` was produced by this rule from a (fictional) v1 YAML with evidence comments.

## 7. Where `curated` sits in the ranking

Ranking: `manufacturer` (4) > `distributor` (3) > `extracted` (2) > `curated` (1). The owner's proposal was
"extracted ≥ curated"; the standard makes it strict.

- A curated dossier is the fallback for a material that has nothing else. If it outranked extraction, the many
  materials with a dose range in their documents could never receive the richer extracted dossier without a
  manual override per material.
- An extracted dossier carries deterministic evidence for every value and is still approved by the same curator
  before it becomes active at Rubedyne. A curated dossier is one person's entry with optional evidence.
- The curator is not overruled silently: a curator-written line (a checklist question, a corrected guidance line)
  lives on inside the extracted dossier as an element with `curated: true` (SPEC 7.2, 8.2 rule 9). A curator who
  disagrees with an extracted value issues a new version of the extracted dossier with that element marked curated.
- "Equal rank" was rejected because equal rank from different publishers means "no automatic replacement"
  (rule 6), which would again block the upgrade.
- A manufacturer dossier always wins, and it cannot contain curated elements. That creates open issue 1.

The owner confirmed the strict ranking and both additions on 2026-11-15. The additions are: an expired distributor
authorization lowers the dossier to the rank of `extracted` (SPEC 8.3), and a withdrawn dossier lets the next
strongest candidate become active (8.2 rule 8).

## 8. Open issues

### Owner decisions of 2026-11-15

| Issue | Decision | Where |
|---|---|---|
| 1 Curator lines vs a manufacturer dossier | (a) A consumer-side overlay that belongs to the material and survives the replacement of the dossier. Publisher guidance and checklist lines are display-only until a curator adopts them one by one; an adopted line becomes overlay content. | SPEC 14.5, 8.2 rule 9 |
| 2 Curated below extracted | Confirmed, together with the two additions in section 7. | SPEC 8.2, 8.3 |
| 3 Phase letters | A separate cold-process marker. The stage `cold_process` carries `usage_view_process: "cold"`, the usage view gets `process: "cold"`, and the view is complete without a phase letter. The v1 playbook validator must accept this before such a usage view can be stored; that change belongs to the implementation. | SPEC 6.1, `vocab/process-stages.json`, checker |
| 4 Facts to verify | Verified against primary sources on 2026-11-15 and re-checked on 2026-11-20; see the CHANGELOG. | vocab, example 03 |
| 5 Governance | Rubedyne decides on vocabulary proposals and issues vocabulary versions. Schemas are served at their `$id` URLs under `rubedyne.com/schemas/material-dossier/<version>/`; vocabulary files have no `$id` and are served at the `base` of `vocab/index.json` followed by the file name. The full licence texts are in `LICENSE-CC-BY-4.0.txt` and `LICENSE-APACHE-2.0.txt`. Protection of the name was not decided. | SPEC 13.3, README |
| 6 Well-known URL | Not registered in 1.0. Consumers must not rely on registration. | SPEC 9.1 |
| 7 Restricted access brokering | Not decided; a product decision for later. | — |
| 8 Signature | Optional in 1.0; planned to be required for the manufacturer route from 1.1. | SPEC 9.5 |
| 9 Thresholds | The proposed values stay (24 months, 5 years, 12 months, the size limits). | SPEC 14.4, 15 |
| 10 Storage | Storage, serving and the curator's approval are outside the standard. Rubedyne's implementation is designed separately. | — |
| 11 Publication | A public landing page at `rubedyne.com/material-dossier`: the specification, the publisher guide, the examples and a downloadable ZIP of the release (spec, schemas, vocabularies, examples, checker, licences). The standard also gets a **public repository**, which becomes its source of truth; releases are tags, and the ZIP, the `$id` files and the copy in Rubedyne's implementation are all built from a tag. The full licence texts and the fact re-check (issue 4) were completed first. The repository is public as public draft 5, tag `v1.0.0-draft.5`, and the landing page is at `rubedyne.com/material-dossier`. | README, LICENSE.md |
| 12 Regulated basis content | **Decided 2026-11-16.** A property `key: "composition.regulated_basis_content"` (dimension `mass_fraction`, forms `exact`/`range`/`limit`, `subject.kind: "neat"`, basis `specification`, `declared`, `typical` or `measured`, no `scope` or `conditions`) with a new member `analyte: {"code": …}` whose code comes from the new vocabulary `vocab/regulated-bases.json` (eight elements and silver chloride; `kind`, `symbol`, `cas`, `aliases`, `annex_examples`). An element code is the total of the element in the material as supplied, from all sources; narrowing to a species is the calculation's job. The relative forms ("as acid", "as free base", "as hydrochloride", "H2O2 present or released", "Retinol Equivalent" …) have no code, because a consumer computes them from the molecular formula. SPEC 7.3 gets rule 6: a quote covering `/analyte` names the analyte by its symbol or an alias. The 43 basis phrases of the Annexes are mapped in `tools/conformance/regulated_basis_phrases.json`. **Why a member, not a condition with `code`** (the idiom of `endpoint` and `sensory_attribute`): whether the analyte is required is decided per key, by the key's term, and a consumer's projection reads it from one fixed place. A condition is an optional qualifier from an open list that no key can make required, and a reader would have to search the list for it. **Why not a composition component:** component contents take part in the composition sums (SPEC 5.4, rule R5 of the checker). Silver counted as Ag is not a separate part of silver chloride on titanium dioxide; as a component it would be counted twice and break the minimum and maximum sums. The projection per material and code, and manual declarations for materials without a dossier, belong to the implementation, not to the standard. | SPEC 5.5.1, 5.5.6, 6.3, 7.3; `vocab/regulated-bases.json`, `vocab/property-keys.json`; example 06; checker |

### The list as written on 2026-11-14

Needing the owner:

1. **Curator lines versus a manufacturer dossier.** When a manufacturer dossier replaces a curated or extracted
   one, Rubedyne's own checklist and guidance lines cannot live inside it. Options: (a) keep them as a
   Rubedyne-side overlay outside the dossier, merged into the usage view at render time; (b) drop them and use the
   manufacturer's lines after per-line approval; (c) both. The standard only says publisher free text needs
   individual human approval before it reaches a prompt (14.2). This decides how the prompt path is built.
2. **Curated below extracted** (section 7), and the two additions named there.
3. **Phase letters.** A–E are Rubedyne's convention and are now in the open vocabulary as `usage_view_phase`. A
   material that is only cold-processed or only pre-dispersed has no letter and cannot reach L1. Either extend the
   letter set, map `cold_process` to an existing letter, or accept the gap.
4. **Facts to verify before release.** The CosIng function list, the ISO / OECD / Ph. Eur. designations in
   `test-methods.json`, the region codes, the regulatory schemes and the illustrative regulatory values in example 03
   were verified against primary sources on 2026-11-15 and re-checked on 2026-11-20; see the CHANGELOG.
5. **Governance.** Who accepts vocabulary proposals and how often a vocabulary version is cut; where the schemas
   and vocabularies are served so that the `$id` URLs resolve; full licence texts; whether "Rubedyne Material
   Dossier" is to be protected as a name.
6. **Well-known URL.** `/.well-known/material-dossier/` is not registered with IANA (RFC 8615). Register it or
   accept an unregistered suffix.
7. **Restricted access.** The standard says "bearer token" and leaves issuance to the publisher. Whether Rubedyne
   wants to broker partner access (one token for many manufacturers) is a product decision.
8. **Signature.** Optional in 1.0. Decide whether 1.1 requires it for the manufacturer route.
9. **Thresholds.** 24 months for regulatory data and five years for anything (SPEC 14.4), the size limits in
   SPEC 15 and the 12 months a withdrawn entry stays listed are proposals.
10. **Storage.** How an implementation stores dossiers next to its earlier playbook data is outside the standard.
11. **Publication.** Where and how the standard is published; added on 2026-11-15, see the table above.

Technical, no decision needed yet:

12. **Evidence check on real documents.** The check is specified and passes on a clean fictional page. The review's
    concerns stand: two-column pages interleave in text extraction, and the drop rate has not been measured on a
    hand-checked sample of real documents. The limit-operator check accepts "min" as a word, which also matches
    "10 min"; the quote limit is 400 characters against 200 in v1.
13. **Classification is unproven by design.** Key, basis, outcome and nominal codes of an extracted element are
    the extractor's judgement; the standard exempts them from evidence and asks consumers to show that.
14. **Vocabulary coverage.** Decorative cosmetics, oral care and fragrance are thin. `interaction-classes` and
    `endpoints` will grow first.
15. **Dataset size and shape.** Points are tuples in axis order, up to 5000 per series; spectra with more points
    need a decision (downsample or raise the limit).
16. **Read-across and multi-material documents** are covered by `read_across_from` and by one dossier per grade,
    but a letter that covers 17 products becomes a source document referenced by 17 dossiers; the standard has no
    shared-document mechanism beyond the same `sha256`.
17. **The checker** does not implement SPEC 8.3 (authorization expiry) and checks restricted-superset-of-public
    only through the examples, not as a two-file comparison.

## 9. Validation

Run `python tools/conformance/run_all.py`. CI runs it on every push to `main` and `devel` and on pull requests.

### Results (2026-11-20, exit status 0)

```
## 1. schemas and vocabularies
PASS schemas
PASS vocabularies
PASS duplicate keys
PASS vocab index
PASS basis enumeration
## 2. examples
OK   01-humectant-active.json  route=manufacturer claimed=L3 computed=L3  properties=33 datasets=1 formulations=2 studies=1 relations=3 attestations=7 statements=8 media=5
OK   01-humectant-active.restricted.json  route=manufacturer claimed=L3 computed=L3  properties=34 datasets=1 formulations=2 studies=1 relations=3 attestations=7 statements=9 media=6
OK   02-rheology-modifier.json  route=manufacturer claimed=L3 computed=L3  properties=30 datasets=3 formulations=1 studies=1 relations=5 attestations=6 statements=6 media=3
OK   03-uv-filter.json  route=manufacturer claimed=L2 computed=L2  properties=29 datasets=1 formulations=2 studies=1 relations=3 attestations=5 statements=4 media=2
OK   04-extracted-emollient.json  route=extracted claimed=L1 computed=L1  properties=11 datasets=1 statements=3 media=2
OK   05-minimal-l1-curated.json  route=curated claimed=L1 computed=L1  properties=6 statements=2 media=1
OK   06-extracted-silver-chloride-tio2.json  route=extracted claimed=L1 computed=L1  properties=5 statements=1 media=1
PASS examples
## 3. endpoint index
OK   index.json  index
PASS endpoint index
## 4. conformance cases
PASS unknown top-level key -> /: schema: 'runbook_id' does not match any of the regexes: '^x-[a-z0-9][a-z0-9.-]*:[a-z0-9][a-z0-9_.-]*$'
PASS numeric value without unit -> /properties/0: schema: 'unit' is a required property
PASS two value forms at once -> /properties/0/value: schema: {'range': {'min': 1, 'max': 5}, 'exact': 3} has too many properties
PASS regulatory limit without region -> /properties/5: schema: 'scope' is a required property
PASS restricted element in the public representation -> /statements/0/visibility: schema: 'public' was expected
PASS property key not in vocabulary -> /properties/0(use-level): 'use.levle' is not in vocabulary property-keys
PASS unit of the wrong dimension -> /properties/0(use-level): unit mPa.s is not accepted for use.level (dimension mass_fraction: %, [ppm], [ppb], mg/kg, ug/g, g/kg, g/(100.g))
PASS implausible use level (500 %) -> /properties/0(use-level): value 500 % is outside the plausible range of use.level [0, 100]
PASS pH 15 -> /properties/5(use-ph): value 15 [pH] is outside the plausible range of use.ph_window [0, 14]
PASS nominal code from the wrong set -> /properties/9(form): nominal code 'humectant' is not in set physical_form
PASS SPF without a test formulation -> /properties/20(spf-f1): uv_performance: the result must be tied to a test formulation
PASS SPF with partially disclosed formulation -> /properties/20(spf-f1): uv_performance: the formulation must disclose every UV filter and booster with its %
PASS SPF without method -> /properties/20(spf-f1): uv_performance: method.standard (or non_standard: true) is required
PASS SPF boost without comparator -> /properties/22(spf-boost): uv.spf_boost: comparison.ref must name the comparator formulation
PASS efficacy result without outcome -> /properties/31(eff-tewl): efficacy: outcome is required
PASS viscosity of a dispersion without shear conditions -> /properties/16(spec-visc): rheology: shear_rate or rotation_speed is required
PASS dangling reference -> /properties/31: reference 'st-missing' does not resolve
PASS formulation not adding up -> /formulations/0(f-gelcream): a fully disclosed formulation must add up to 100 % (is 24.11)
PASS composition minima above 100 -> /composition: the minimum contents add up to 114 %
PASS L3 claim with a figure-only dataset -> /conformance_level: claims L3 but reaches L2: a dataset has a figure but no numeric series; declarations.negative_results_included is not true; comple
PASS L2 claim on a minimal dossier -> /conformance_level: claims L2 but reaches L1: no composition; no profile.function; no profile.physical_form; fewer than three specification or typical
PASS minimal dossier without phase -> /conformance_level: below L1: no use.phase that maps to a phase letter or to process cold
PASS curated flag in a manufacturer dossier -> /statements/0: curated: true is allowed only in extracted or curated dossiers
PASS expired-style certificate without valid_until -> /attestations/5(att-cosmos): a certified attestation needs issuer and valid_until
PASS extracted element without evidence -> /properties/10: schema: {'id': 'shelf', 'as_of': '2025-03-10', 'key': 'stability.shelf_life', 'basis': 'specification', 'subject': {'kind': 'neat'}, '
PASS extracted number not in its quote -> /properties/4(spec-acid): the number 0.2 at /value/limit/value is in none of its quotes
PASS extracted quote not on the page -> /properties/10(shelf): evidence[0]: quote is not verbatim on page 2 of 'doc-tds'
PASS extracted leaf not covered -> /properties/7(typ-density): no evidence covers /unit
PASS extracted limit turned into a different operator -> /properties/6(spec-water): the limit operator >= at /value/limit/op is in none of its quotes
PASS extracted dataset with points -> /datasets/0/points_origin: schema: 'publisher_raw' is not one of ['tabulated', 'none']
PASS extracted CAS number not in its quote -> /identity: the identifier '9999-99-9' at /cas/0 is in none of its quotes
PASS extracted trade name not in its quote -> /identity: the identifier 'Exaester GX' at /trade_name is in none of its quotes
PASS thousands separator proves nothing -> /properties/9(typ-spread): the number 2.5 at /value/exact is in none of its quotes
PASS basis content without analyte -> /properties/0(basis-ag): composition.regulated_basis_content needs analyte
PASS analyte code not in the vocabulary -> /properties/0(basis-ag): analyte code 'element.xx' not in vocabulary regulated-bases
PASS analyte on a key without one -> /properties/2(spec-water): analyte is not allowed for physchem.water_content
PASS basis content of a dilution -> /properties/0(basis-ag): composition.regulated_basis_content is stated for the material as supplied (subject neat)
PASS basis content as a recommendation -> /properties/0(basis-ag): basis recommended is not allowed for composition.regulated_basis_content
PASS basis content with a scope -> /properties/0(basis-ag): composition.regulated_basis_content takes no scope or conditions
PASS analyte not covered by evidence -> /properties/0(basis-ag): no evidence covers /analyte
PASS quote does not name the analyte -> /properties/0(basis-ag): the analyte element.ag is in none of its quotes

PASS precedence: extracted replaces curated -> True (stronger source)
PASS precedence: curated replaces extracted -> False (weaker source never replaces a stronger one)
PASS precedence: manufacturer replaces extracted -> True (stronger source)
PASS precedence: extracted replaces manufacturer -> False (weaker source never replaces a stronger one)
PASS precedence: distributor replaces manufacturer -> False (weaker source never replaces a stronger one)
PASS precedence: manufacturer replaces distributor -> True (stronger source)
PASS precedence: newer manufacturer version replaces older -> True (newer version of the same dossier)
PASS precedence: older manufacturer version replaces newer -> False (not a newer version)

50/50 expectations met
PASS phrase map: 43 phrases, 43 entries -> all mapped
PASS rule6 vectors: 16 passed, 0 failed
PASS empty conditions on basis content -> no error
PASS conformance cases
PASS: 0 failed check(s)
```

Step 4 runs 42 mutations of the valid examples, each of which must be refused with the expected message, and 8
precedence cases: 50 expectations. The mutations include: unknown top-level member; numeric value without unit; two
value forms at once; regulatory limit without region; restricted element in a public representation; misspelled
property key; unit of the wrong dimension; use level of 500 %; pH 15; nominal code from the wrong set; SPF without a
test formulation; SPF with a partially disclosed formulation; SPF without a method; SPF boost without comparator;
efficacy result without outcome; viscosity of a dispersion without shear conditions; dangling reference; fully
disclosed formulation not adding up to 100 %; composition minima above 100 %; L3 claimed with a figure-only dataset;
L2 claimed on a minimal dossier; minimal dossier without a phase; `curated: true` in a manufacturer dossier;
certified attestation without validity; extracted element without evidence; extracted number not in its quote; quote
not on the page; uncovered leaf; changed limit operator; extracted dataset with points; thousands separator offered
as proof. Precedence: the eight combinations of section 7 and SPEC 8.2.

On 2026-11-14 the usage views of the six examples that existed then were also checked against the v1 playbook
validator, which is not part of this repository, and every round trip from a v1 playbook to an L1 dossier and
back to the usage view was equal. Example 06 was added later and has not been through that check.

One finding from this verification changed the standard: the first round-trip run failed for `phase: [e, b]`,
because the usage view sorted the letters while v1 keeps the declared order. SPEC 6.1 now says "document order".

### What was not verified

- No dossier was produced from a real document, and no real publisher endpoint exists; the endpoint protocol
  (SPEC 9) is specified but exercised only through the index file and its hashes.
- The restricted representation was validated as a document; that it is a superset of the public one was checked
  by construction (it is generated from it), not by the checker.
- The detached signature (SPEC 9.5) has no example and no test.
- The evidence check ran against two clean fictional text pages, not against `pdftotext` output of real PDFs.
- Vocabulary contents were compared with their external sources on 2026-11-15 and 2026-11-20; the CHANGELOG lists
  what could not be verified.
