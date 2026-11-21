# Rubedyne Material Dossier

An open, machine-readable format for the complete structured document of **one cosmetic raw material**.

A raw-material manufacturer publishes one JSON document per sellable grade: identity, composition, specifications,
use, functions, studies, interactions, starting formulations, stability, safety, regulatory status, certifications,
figures. Formulation software, PIF tools and distributors read it directly. The brochure, the technical data sheet
and the PDF attachments stop being the carrier of the data.

Status: **1.0, public draft for feedback (tag v1.0.0-draft.3).** Landing page:
[rubedyne.com/material-dossier](https://rubedyne.com/material-dossier).

Start with `SPEC.md` sections 1 to 3, `guides/publisher-guide.md` and `examples/`. Release:
https://github.com/Rubedyne/material-dossier/releases/tag/v1.0.0-draft.3.

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
   attestation, and statement with media (counted as one). A property always says what was measured (`subject`),
   in what sense the value holds (`basis`), and has exactly one value form (exact, range, limit, nominal, text,
   in-figure).
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
| `schema/dossier.schema.json` | JSON Schema, draft 2020-12, of a dossier. |
| `schema/index.schema.json` | JSON Schema of a publisher's endpoint index. |
| `schema/vocab.schema.json` | JSON Schema of a vocabulary file. |
| `vocab/*.json` | The 24 vocabularies (895 keys), version 1.0; `vocab/index.json` lists them. |
| `examples/` | Fictional dossiers that validate (see below) and an endpoint index. |
| `guides/publisher-guide.md` | How to turn a brochure or TDS into a dossier, field by field. |
| `tools/check_dossier.py` | Reference checker (non-normative): schema, vocabulary, view rules, evidence, usage view, index. |
| `tools/conformance/` | `run_all.py` (runs every check), `mutation_cases.py` (the conformance cases), `rule6_vectors.json` (the evidence rule 6 vectors), `regulated_basis_phrases.json` with its source list `annex-basis-phrases-2026-11-16.md` (the Annex basis phrase map), `check_identity.py` (checks that every commit has the project identity). |
| `tools/release/build.py` | The release builder (see "Releases"). |
| `tests/` | Tests of the runner, the release builder, the identity check and the issue forms. |
| `DESIGN-NOTES.md` | Decisions, rejected alternatives, migration of Rubedyne's earlier material records ("v1 material playbooks"), open issues, validation log. |
| `README.md` | This overview. |
| `CHANGELOG.md`, `LICENSE.md` | The history of the standard and the vocabularies; which licence covers which files. |
| `LICENSE-CC-BY-4.0.txt`, `LICENSE-APACHE-2.0.txt` | The full licence texts. |
| `README.hu.md` | Short Hungarian overview. |
| `requirements.txt`, `requirements-dev.txt` | Python dependencies: `jsonschema` for the checker and the runner; the dev file adds pytest and PyYAML for the tests. |
| `.github/workflows/conformance.yml` | CI on Python 3.10 and 3.12: runs `run_all.py` and the tests and builds the release, on every push to `main` and `devel` and on pull requests; on pushes it also checks the commit identity. |
| `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/` | How to give feedback and propose vocabulary keys; the issue forms. |
| `.gitignore` | Keeps the virtual environment, caches and `dist/` out of git. |
| `.gitattributes` | Turns off line-ending conversion, so every checkout has the same bytes as the release (and the content hashes in `examples/index.json` hold). |

The release ZIP holds the specification, this README, the CHANGELOG, the licences, the guide, the schemas, the
vocabularies, the examples, the checker with `requirements.txt` and `tools/conformance/`. The tests, the release
builder, `requirements-dev.txt`, `DESIGN-NOTES.md`, `CONTRIBUTING.md`, `README.hu.md`, `.gitattributes` and `.github/`
are only in the repository: https://github.com/Rubedyne/material-dossier.

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
| `05-minimal-l1-curated.json` | The minimal dossier: identity and the usage view only (the shape of a hand-curated record migrated from an older format). |
| `06-extracted-silver-chloride-tio2.json` | Extracted dossier, L1: the content of two regulated bases (silver as Ag, a specification range; silver chloride, a typical value) that stoichiometry cannot compute for silver chloride on titanium dioxide. `sources/doc-agcl.p1.txt` is its page text. |
| `index.json` | The endpoint index of the fictional manufacturer "Example Ingredients Ltd.": it lists 01 (public and restricted), 02 and 03 with their content hashes, and one withdrawn dossier without a file. The extracted and curated examples (04, 05, 06) are not a manufacturer's and are not listed. |

## Checking a dossier

Prerequisites: git, Python 3.9 or newer (CI runs 3.10 and 3.12) and network access for pip; the release comparison
below also uses `curl`, `cmp` and `sha256sum`. All commands run from the repository root.

```bash
git clone https://github.com/Rubedyne/material-dossier.git
cd material-dossier
```

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python tools/check_dossier.py examples/01-humectant-active.json
.venv/bin/python tools/check_dossier.py --sources examples/sources examples/04-extracted-emollient.json
.venv/bin/python tools/check_dossier.py --usage-view examples/05-minimal-l1-curated.json
.venv/bin/python tools/check_dossier.py --index examples/index.json
```

A dossier check prints one line per file,
`OK   01-humectant-active.json  route=manufacturer claimed=L3 computed=L3 …`, and exits 0; the index check prints
`OK   index.json  index`. On errors the checker prints `FAIL`, one `error` line per problem with its JSON pointer,
and exits 1 (2 for a wrong call). `warning` lines do not change the exit status. `--usage-view` prints the usage
view as JSON instead of the `OK` line.

To check your own dossier, give its path; it can be anywhere:

```bash
.venv/bin/python tools/check_dossier.py path/to/your-dossier.json
```

For an extracted dossier, add `--sources DIR` with the page texts as `DIR/<media id>.p<page>.txt`; without it the
quotes are not verified against the pages.

The checker reports schema errors, unknown vocabulary keys, broken references, implausible values, view-rule
violations (for example an SPF value without its test formulation), evidence that does not hold, and the conformance
level the dossier actually reaches.

To run every check at once:

```bash
.venv/bin/python tools/conformance/run_all.py
```

It checks the schemas and vocabularies (with duplicate keys, the vocabulary index and the `$id` layout), every
example, the endpoint index and the conformance cases: the broken variants the checker must reject, the precedence
cases, the evidence rule 6 vectors and the Annex basis phrase map. It prints one `PASS` or `FAIL` line per check,
reports `49/49 expectations met` for the conformance cases, ends with `PASS: 0 failed check(s)` and exits 0.

The tests need the dev requirements:

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q tests
```

The test run ends with `25 passed`.

## How the vocabularies grow

- Vocabularies are closed: a key that is not in the vocabulary is an error, which is what catches typing mistakes.
- When a publisher needs a key that does not exist, it uses a namespaced extension key, `x-<its domain>:<name>`.
  Consumers store and show it but do not interpret it.
- Extension keys that prove useful are proposed for the next vocabulary minor version (`vocab_version` 1.1, 1.2, …).
  A proposal names the key, its definition, the value forms and the unit dimension (for property keys) and one real
  use; it is made with the "Vocabulary proposal" issue form (see `CONTRIBUTING.md`).
- Rubedyne, the standard's owner, decides on proposals and issues the vocabulary versions.
- Keys are never removed and never change meaning. A superseded key is marked `deprecated` with `replaced_by`.
- Where an external vocabulary exists it is used instead of a new one: UCUM (units), CosIng (INCI names,
  functions), ISO / OECD / pharmacopoeia numbers (methods), ISO 3166 (countries), BCP 47 (languages), SPDX
  (licences).

Version 1.0 of the vocabularies is reasonably complete for skin care, hair care, sun care and preservation; it is
not exhaustive. The thinnest areas are decorative cosmetics, oral care and fragrance.

## Contributing

Feedback on the draft and proposals for vocabulary keys go through the two issue forms, "Draft feedback" and
"Vocabulary proposal": https://github.com/Rubedyne/material-dossier/issues/new/choose.
Pull requests are not merged; Rubedyne writes every change and, if asked, credits the proposer in the CHANGELOG.
See `CONTRIBUTING.md` for the route, the licence of contributions and what not to post.

## Releases

Releases are tags (`v1.0.0-draft.3`, …); the version is the tag without the leading `v`. Each GitHub release
carries the ZIP and `SHA256SUMS.txt`, and those assets are canonical. The schemas and vocabularies are served at
their `$id`, under `https://rubedyne.com/schemas/material-dossier/1.0/`.

The build is deterministic: the same tag gives the same bytes on any machine and at any time. To rebuild a release
and compare it with the published checksums:

```bash
git checkout v1.0.0-draft.3
python3 tools/release/build.py --version 1.0.0-draft.3 dist/1.0.0-draft.3
curl -sL -o dist/SHA256SUMS.published.txt \
  https://github.com/Rubedyne/material-dossier/releases/download/v1.0.0-draft.3/SHA256SUMS.txt
cmp dist/SHA256SUMS.published.txt dist/1.0.0-draft.3/SHA256SUMS.txt && echo identical
```

The builder writes into the output folder the ZIP `material-dossier-<version>.zip`, the files served under each
`$id` (`schemas/material-dossier/1.0/*.schema.json` and the vocabularies under
`schemas/material-dossier/1.0/vocab/1.0/`) and `SHA256SUMS.txt`, which lists all of them. It refuses, with exit
status 2, when the git work tree has uncommitted or untracked files, when the output folder exists and is not
empty, or when the version is neither `1.0.0` nor `1.0.0-draft.N`.

To verify a downloaded ZIP, run `sha256sum -c --ignore-missing SHA256SUMS.txt` in the folder that holds both files.

## Licence

Specification text and guides: CC BY 4.0. JSON Schemas, vocabularies, tools, examples and tests: Apache-2.0.
The full texts are in `LICENSE-CC-BY-4.0.txt` and `LICENSE-APACHE-2.0.txt`. See `LICENSE.md`.
