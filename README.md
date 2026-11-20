# Rubedyne Material Dossier

An open, machine-readable format for the complete structured document of **one cosmetic raw material**.

A raw-material manufacturer publishes one JSON document per sellable grade: identity, composition, specifications,
use, functions, studies, interactions, starting formulations, stability, safety, regulatory status, certifications,
figures. Formulation software, PIF tools and distributors read it directly. The brochure, the technical data sheet
and the PDF attachments stop being the carrier of the data.

Status: **1.0, draft (2026-11-14).** Published as the draft tag v1.0.0-draft.1; not yet released.

## Who it is for

| You are | Read |
|---|---|
| A raw-material manufacturer or distributor who wants to publish dossiers | `guides/publisher-guide.md`, then the examples |
| A developer who consumes dossiers | `SPEC.md` (sections 8, 9, 11, 14, 15), the schemas, `tools/check_dossier.py` |
| Deciding whether to adopt it | this file and `DESIGN-NOTES.md` |
| A Hungarian reader | `README.hu.md` |

## The idea in five lines

1. **One dossier = one sellable grade.** A product family is only an optional label.
2. **Nine primitives** carry everything: identity, composition, property, dataset, formulation, study, relation,
   attestation, statement and media. A property always says what was measured (`subject`), in what sense the value
   holds (`basis`), and has exactly one value form (exact, range, limit, nominal, text, in-figure).
3. **Closed vocabularies** (functions, endpoints, property keys with canonical units, …) carry the variety; they
   are versioned separately and only grow.
4. **Views** are rule packs over the primitives. The **usage view** (use level, phase, pH window, maximum
   temperature, a few guidance and checklist lines) is the part formulation tools check against; a material with
   nothing else known still has a minimal dossier with just that.
5. **The source is always recorded** and ranked: manufacturer > authorized distributor > extracted from documents >
   curated by hand. A weaker source never replaces a stronger one.

## Repository layout

| Path | Content |
|---|---|
| `SPEC.md` | The normative specification. |
| `schema/dossier.schema.json` | JSON Schema (draft 2020-12) of a dossier. |
| `schema/index.schema.json` | JSON Schema of a publisher's endpoint index. |
| `schema/vocab.schema.json` | JSON Schema of a vocabulary file. |
| `vocab/*.json` | The vocabularies, version 1.0; `vocab/index.json` lists them. |
| `examples/` | Fictional dossiers that validate (see below) and an endpoint index. |
| `guides/publisher-guide.md` | How to turn a brochure or TDS into a dossier, field by field. |
| `tools/check_dossier.py` | Reference checker (non-normative): schema, vocabulary, view rules, evidence, usage view, index. |
| `tools/conformance/` | `run_all.py` (runs every check), `mutation_cases.py` (the conformance cases), `rule6_vectors.json` (the evidence rule 6 vectors), `regulated_basis_phrases.json` with its source list (the Annex basis phrase map). |
| `tests/` | Tests of the runner. |
| `DESIGN-NOTES.md` | Decisions, rejected alternatives, migration of Rubedyne's v1 material playbooks, open issues, validation log. |
| `CHANGELOG.md`, `LICENSE.md` | |
| `LICENSE-CC-BY-4.0.txt`, `LICENSE-APACHE-2.0.txt` | The full licence texts. |
| `README.hu.md` | Short Hungarian overview. |
| `requirements.txt`, `requirements-dev.txt` | Python dependencies: `jsonschema` for the checker and the runner; the dev file adds pytest for the tests. |
| `.github/workflows/conformance.yml` | CI: runs `run_all.py` and the tests on every push. |

## Examples

Everything in `examples/` is invented. "Example Ingredients Ltd.", "Example Minerals Ltd.", their trade names,
product codes, studies and numbers do not exist; values are illustrative and must not be used as data. INCI names
and test standards are the generic public ones.

| File | Shows |
|---|---|
| `01-humectant-active.json` | Manufacturer dossier, L3: composition with origin, specification, in vivo hydration study with a time-course dataset and an endpoint without effect, a measured interaction, COSMOS approval with a usage restriction. |
| `01-humectant-active.restricted.json` | The restricted representation of the same version: exact composition, an assay specification, the full study report. |
| `02-rheology-modifier.json` | Manufacturer dossier, L3: viscosity against concentration and against pH as numeric series, an ordinal compatibility table, a starting formulation with procedure and stability results. |
| `03-uv-filter.json` | Manufacturer dossier, L2: SPF in vivo, UVA-PF, critical wavelength, water resistance and SPF boost, each tied to a fully disclosed test formulation; a figure without data, marked as such; regional limits. |
| `04-extracted-emollient.json` | Extracted dossier, L1: field-level evidence for every value, a figure-only dataset, one curator-written line. `sources/doc-tds.p1.txt` and `.p2.txt` are the (fictional) page texts the quotes are checked against. |
| `05-minimal-l1-curated.json` | The minimal dossier: identity and the usage view only, migrated from a v1 material playbook. |
| `06-extracted-silver-chloride-tio2.json` | Extracted dossier, L1: the content of two regulated bases (silver as Ag, a specification range; silver chloride, a typical value) that stoichiometry cannot compute for silver chloride on titanium dioxide. `sources/doc-agcl.p1.txt` is its page text. Not listed in `index.json`, which belongs to the fictional manufacturer. |
| `index.json` | The endpoint index of the fictional manufacturer, with content hashes of the files above. |

## Checking a dossier

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python tools/check_dossier.py examples/01-humectant-active.json
.venv/bin/python tools/check_dossier.py --sources examples/sources examples/04-extracted-emollient.json
.venv/bin/python tools/check_dossier.py --usage-view examples/05-minimal-l1-curated.json
.venv/bin/python tools/check_dossier.py --index examples/index.json
```

To run every check at once (schemas, vocabularies, examples, the endpoint index and the conformance cases):

```bash
.venv/bin/python tools/conformance/run_all.py
```

The checker reports schema errors, unknown vocabulary keys, broken references, implausible values, view-rule
violations (for example an SPF value without its test formulation), evidence that does not hold, and the conformance
level the dossier actually reaches.

## How the vocabularies grow

- Vocabularies are closed: a key that is not in the vocabulary is an error, which is what catches typing mistakes.
- When a publisher needs a key that does not exist, it uses a namespaced extension key, `x-<its domain>:<name>`.
  Consumers store and show it but do not interpret it.
- Extension keys that prove useful are proposed for the next vocabulary minor version (`vocab_version` 1.1, 1.2, …).
  A proposal names the key, its definition, the value forms and the unit dimension (for property keys) and one real
  use.
- Rubedyne, the standard's owner, decides on proposals and issues the vocabulary versions.
- Keys are never removed and never change meaning. A superseded key is marked `deprecated` with `replaced_by`.
- Where an external vocabulary exists it is used instead of a new one: UCUM (units), CosIng (INCI names,
  functions), ISO / OECD / pharmacopoeia numbers (methods), ISO 3166 (countries), BCP 47 (languages), SPDX
  (licences).

Version 1.0 of the vocabularies is reasonably complete for skin care, hair care, sun care and preservation; it is
not exhaustive. The thinnest areas are decorative cosmetics, oral care and fragrance.

## Releases

Releases are tags (`v1.0.0-draft.2`, ...). From a clean checkout of a tag,

```
python3 tools/release/build.py --version <version> dist/<version>
```

builds the ZIP and the files served under each schema's `$id`. Each GitHub release carries the ZIP and
`SHA256SUMS.txt`, and those assets are canonical.

## Licence

Specification text and guides: CC BY 4.0. JSON Schemas, vocabularies, tools, examples and tests: Apache-2.0.
The full texts are in `LICENSE-CC-BY-4.0.txt` and `LICENSE-APACHE-2.0.txt`. See `LICENSE.md`.
