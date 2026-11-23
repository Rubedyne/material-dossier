# Changelog

The standard (`standard_version`) and the vocabularies (`vocab_version`) are versioned separately.
Within 1.x both only add (SPEC.md sections 13.2 and 13.3).

## Standard

### 1.0 — public draft 5, 2026-11-23

Tag `v1.0.0-draft.5`. The rules and examples are unchanged; one dimension is added (see Vocabularies, 2026-11-23).

- SPEC 4.3 rule 6: an ISO 16128 index (dimension `fraction`) is a number from 0 to 1 in the canonical unit `1`;
  `%` is accepted, as documents state it (58.3 % is 0.583). Dossiers that give the index in `1` stay valid.
- One conformance case: an index of 158 % is refused as outside 0 to 1 after conversion (50 expectations in all).

### 1.0 — public draft 4, 2026-11-21

Tag `v1.0.0-draft.4`. The rules, keys and examples of the standard are unchanged.

- `.gitattributes` keeps the released bytes on every checkout (line endings): a clone with `core.autocrlf=true`
  passes the checks on the examples and rebuilds the same release.
- Vocabulary files are served at the `base` of `vocab/index.json`, not at an `$id` (README "Releases", SPEC 13.3
  rule 5, DESIGN-NOTES issue 5).
- A test ties the named tag to the changelog: every draft tag named in the repository outside `CHANGELOG.md`
  (`v1.0.0-draft.N`, also without the `v`) equals the tag of the top changelog entry; the placeholder version of
  the CI build is exempt.

### 1.0 — public draft 3, 2026-11-20

Tag `v1.0.0-draft.3`. The rules, keys and examples of the standard are unchanged.

- README: prerequisites, the clone step, expected outputs, the test command, how to rebuild a release and compare
  it with the published `SHA256SUMS.txt`, the repository layout.
- Publisher guide section 8: the checker command with its setup. README.hu.md: the current file list.

### 1.0 — public draft 2, 2026-11-20

Tag `v1.0.0-draft.2`, the public draft for feedback. The rules, keys and examples of the standard are unchanged.

- Release builder: `tools/release/build.py` builds, from a clean checkout of a tag, the distribution ZIP, the
  files served under each schema's `$id` and `SHA256SUMS.txt`, byte for byte the same on every run.
- `$id` layout: everything of a version is served under `https://rubedyne.com/schemas/material-dossier/1.0/`;
  the vocabulary `base` in `vocab/index.json` is now `https://rubedyne.com/schemas/material-dossier/1.0/vocab/1.0/`
  (was `…/material-dossier/vocab/1.0/`).
- Pinned CI: the GitHub Actions are pinned by commit; CI also builds the release and checks that every commit
  has the project identity.
- Contribution route: `CONTRIBUTING.md` and two issue forms, "Draft feedback" and "Vocabulary proposal".
  Rubedyne decides on proposals (SPEC 13.3 rule 3); pull requests are not merged.

### 1.0 — draft, 2026-11-14

First version. Published as the draft tag `v1.0.0-draft.1`; not yet released.

- Nine primitives: identity, composition, property, dataset, formulation, study, relation, attestation,
  statement / media.
- Property core: mandatory `basis` and `subject`, closed `value` union (exact, range, limit, nominal, text,
  in_figure), UCUM units with canonical units per key.
- Views with rules: usage, profile, specification, efficacy, interaction, uv_performance, rheology, preservation,
  safety, regulatory, fragrance, sustainability, stability.
- The usage view as a normative projection, and the minimal L1 dossier (identity + usage view).
- Four source routes (manufacturer, distributor, extracted, curated) with a precedence rule; field-level evidence
  for extracted dossiers.
- Public and restricted representations.
- Publisher endpoint: index at `/.well-known/material-dossier/index.json`, content hash, optional detached
  signature.
- Conformance levels L1 to L3.
- Schemas: `dossier.schema.json`, `index.schema.json`, `vocab.schema.json`.

#### Owner decisions of 2026-11-15 (DESIGN-NOTES section 8)

- Usage view: `process: "cold"` for the stage `cold_process`; such a view is complete without a phase letter.
- Consumer overlay (SPEC 14.5): consumer content that belongs to the material, outside the dossier.
- The `.well-known` suffix is unregistered in 1.0 (SPEC 9.1). Signatures are planned to be required for the
  manufacturer route in 1.1 (SPEC 9.5).
- Governance and schema hosting (SPEC 13.3 rules 3 and 5).

#### Owner decision of 2026-11-16: evidence rule 5

- Evidence rule 5 (SPEC 7.3): an identifier of the identity or of a composition component (trade name, product
  code, INCI, CAS, EC …) must occur in a quote that covers it. Before, any verbatim quote proved a text value.

#### Owner decision of 2026-11-16: regulated basis content (DESIGN-NOTES section 8, issue 12)

- The property key `composition.regulated_basis_content` and the property member `analyte: {code}` (SPEC 5.5.6,
  6.3): the content, in the material as supplied, of the element or named substance in which a regulatory limit
  is expressed, where stoichiometry cannot compute it. `subject.kind` `neat`; basis `specification`, `declared`,
  `typical` or `measured`; no `scope` or `conditions`; a `mass_fraction` unit. A property-key term that names a
  vocabulary in `analyte` makes the member required; on any other key it is an error. An extension code is stored
  with a warning and not projected.
- Evidence rule 6 (SPEC 7.3): a quote that covers `/analyte` must name the analyte by its symbol or an alias.
  `tools/conformance/rule6_vectors.json` holds 16 quotes that pin the symbol and alias matching down; the
  conformance script runs them.
- Non-normative guidance on reading the content (SPEC 6.3): the highest stated value, its certainty, stale `as_of`.
- Example 06 (extracted, silver chloride on titanium dioxide) and eight conformance cases (49 expectations in all).
  `tools/conformance/regulated_basis_phrases.json` maps the 43 basis phrases of Annex III, V and VI to a code,
  to "stoichiometric" or to "not_a_basis"; the conformance script checks the map.
- Final review, 2026-11-16: an empty `conditions` list (or `scope`) on a basis-content property counts as absent
  (SPEC 5.5.6, 6.3; `tools/check_dossier.py`); rule 6 notes that a symbol match can be a false positive and is
  accepted (SPEC 7.3).
- Additive: that change altered no existing rule, key or example.

#### Repository, 2026-11-20

- The full licence texts: `LICENSE-CC-BY-4.0.txt` and `LICENSE-APACHE-2.0.txt`.
- `tools/conformance/run_all.py` runs every check (schemas, vocabularies, examples, the endpoint index, the
  conformance cases); CI runs it on every push.

## Vocabularies

### 1.0 — draft, 2026-11-14

23 vocabulary files, 885 terms: basis, functions (CosIng), sensory, endpoints, study kinds, interaction effects
and classes, composition roles, origin types, product types and forms, process stages, statement kinds, document
kinds, attestation schemes and statuses, usage restrictions, condition keys, units (dimensions with canonical and
accepted UCUM units), nominal code sets, test methods (bodies and a registry), regions, property keys.

2026-11-15: `process-stages`: `cold_process` carries `usage_view_process: "cold"`.

2026-11-16: new vocabulary `regulated-bases` (9 terms: `element.ag`, `.al`, `.f`, `.hg`, `.s`, `.sr`, `.zn`, `.zr`
and `substance.silver_chloride`, with `kind`, `symbol`, `cas`, `aliases`, `definition`, `annex_examples`; the
relative forms that stoichiometry decides are left out on purpose). `property-keys`:
`composition.regulated_basis_content`, whose term carries the new member `analyte: "regulated-bases"`.
`vocab.schema.json` types the new term members. Now 24 vocabulary files, 895 terms.

2026-11-23: `units`: new dimension `fraction` (canonical `1`; accepted `1` and `%` with factor 0.01).
`property-keys`: the four ISO 16128 indexes (`origin.natural_index`, `origin.natural_origin_index`,
`origin.organic_index`, `origin.organic_origin_index`) move from `dimensionless` to `fraction`; their meaning and
their bounds 0 to 1 are unchanged. `dimensionless` itself takes no percent (HLB, SPF, refractive index). Now 24
vocabulary files, 896 terms.

2026-11-15 fact check against primary sources:

- `functions`: the full CosIng list of functions (83), with CosIng names and descriptions. `emollient` and
  `emulsifying` are kept but marked non-official, pointing to `skin_conditioning_emollient` and
  `surfactant_emulsifying`.
- `test-methods`: every designation exists. ISO 3219 is deprecated in favour of ISO 3219-2. Titles of ISO 2555 and
  OECD 442C/D/E were updated, and ISO 29621, 22716, 22717, 22718, 21150, 18416, 21148 and OECD TG 497, 467 and 491
  were added.
- `regions`: definitions added. `attestation-schemes`: RSPO Book and Claim, the Vegan Society trademark and
  Leaping Bunny were added, and issuers named.
- Example 03: the EU Annex VI entry 25 limit (10 %) and the Australian limit (10 %) were confirmed. The US status
  was updated to the 2026 FDA final order (monograph M020, up to 6 %).
- Not verified first-hand: the Colipa 2005 water-resistance guideline (dead link), Ph. Eur. 12th edition titles,
  the current USP <51> revision, the US effective date, and whether a 2026 Australian determination replaced the
  2025 one (see the 2026-11-20 re-check below for what became of these).

### Fact re-check, 2026-11-20

The facts of the vocabularies and of example 03 were re-checked against primary sources; what was not checked is
listed at the end. The terms and their keys are unchanged: still 24 vocabulary files, 895 terms.

Corrections (labels, definitions and values only; no key, code, symbol or alias changed):

- `functions`, `not_reported`: `definition` is now the CosIng description, "No function currently reported."
  (the editorial parenthetical was removed). Source: CosIng list of functions.
- `test-methods`, `iso:23675`: label "In vitro determination of sun protection factor (SPF)" (the official title of
  ISO 23675:2024; the "double-plate method" part and the lead-in were not in it). Source: iso.org catalogue.
- `test-methods`, `iso:23698`: label "Measurement of the sunscreen efficacy by diffuse reflectance spectroscopy"
  (the official title of ISO 23698:2024). Source: iso.org catalogue.
- `test-methods`, `oecd:401`: label now says "guideline deleted with effect from 17 December 2002" (was "in 2002").
  Source: OECD Council document C(2001)282, which sets the deletion of Guideline 401 to take effect on
  17 December 2002, and the OECD publication page of Test No. 401.
- `attestation-schemes`, `rspo_ip`: definition aligned to the RSPO wording ("from a single identifiable certified
  source, kept separate from conventional material throughout the supply chain"). Source: rspo.org.
- `attestation-schemes`, `rspo_bc`: definition now names the credit sources as RSPO's page does ("RSPO-certified
  growers, crushers or independent smallholders"). Source: rspo.org.
- `attestation-schemes`, `au_aiic`: label "Australia AIIC (AICIS)", naming the administering body. Source:
  industrialchemicals.gov.au.
- `regulated-bases`, `element.ag`: `annex_examples` is now `["V/59"]`. Entry V/52 states its limit as AgCl, not
  as Ag; it stays under `substance.silver_chloride`. Source: Regulation (EC) No 1223/2009, consolidated text of
  2026-05-18.
- Example 03 (its hash and size in `examples/index.json` were recomputed): the Australian reference now names
  Determination (No. 3) 2026 (in force from 2026-10-16; the limit is still 10 %), and `as_of` of `att-au` and
  `reg-au` is 2026-10-16. The US reference now reads "OTC Monograph M020, final order OTC000039 (issued 2026-06-10,
  effective 2026-08-09): up to 6 %". Sources: legislation.gov.au; FDA final administrative order OTC000039.
- Colipa 2005 water-resistance guideline: Cosmetics Europe Recommendation No. 16 (revised June 2023) supersedes it.
  The `colipa:water-resistance-2005` term stays, as its key is protected.

Confirmed first-hand:

- The 83 CosIng functions: names and descriptions match the official list (the typo fixes declared in the
  `functions` source note are the only differences). All 83 have a term.
- The UCUM codes of `units` (checked against the UCUM 2.2 grammar) and their conversion factors.
- The regulated-bases symbols and CAS number (silver chloride 7783-90-6, confirmed through the Regulation text and
  its check digit), and the Annex III and V entries in `annex_examples`; the 43 phrases of
  `regulated_basis_phrases.json` occur in every listed entry.
- Example 03: EU Annex VI entry 25 (bemotrizinol, 10 %); Australia still 10 % under Determination (No. 3) 2026;
  US monograph M020 up to 6 %, effective 2026-08-09.
- The designations of the other test methods, and the ISO 3166 and membership facts of `regions`.

Not verified in this re-check:

- The repeal date of Decision 2006/257/EC. That `emollient` and `emulsifying` are absent from the current CosIng
  list is confirmed.
- 52 terms of `attestation-schemes`. Most carry a label only, with no definition to check, and the scheme owners'
  own pages were not consulted for them. No renamed or withdrawn scheme is known.
- The Ph. Eur. 12th edition titles (licence-only); they match the 11.7 index and no renumbering is known.
- The current USP <51> revision (subscription only); the title is confirmed.
- The body `ectfa` (protected; its label "CTFA / PCRC" could not be verified, so it is unchanged).
