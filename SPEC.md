# Rubedyne Material Dossier — Specification 1.0

| | |
|---|---|
| Standard version | 1.0 (public draft 4 for feedback, 2026-11-21; tag v1.0.0-draft.4) |
| Vocabulary version | 1.0 |
| Schema | `schema/dossier.schema.json`, `$id` `https://rubedyne.com/schemas/material-dossier/1.0/dossier.schema.json` |
| Licence | This text: CC BY 4.0. Schemas, vocabularies and tools: Apache-2.0. See `LICENSE.md`. |

## 1. Scope

A **material dossier** is one JSON document that holds the complete structured description of **one sellable grade
or form** of a cosmetic raw material: identity, composition, specifications, use, functional profile, performance
studies, interactions, starting formulations, stability, safety, regulatory status, certifications, figures and
references to documents.

Its purpose is that a raw-material manufacturer publishes the dossier itself, in a form that software can read
without interpretation, so that brochures, technical data sheets and PDF attachments are no longer the carrier of
the data.

Out of scope: batch data (certificates of analysis), prices, packaging and ordering data, the safety data sheet as
a document (a dossier carries selected SDS values and references the SDS, section 5.12), and anything about a
finished cosmetic product.

## 2. Conformance language and terms

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, RECOMMENDED, MAY and OPTIONAL are to be interpreted as
described in BCP 14 (RFC 2119, RFC 8174) when, and only when, they appear in capitals.

| Term | Meaning |
|---|---|
| Material | One sellable grade or form of a raw material with its own product code. |
| Dossier | The document defined here. One material has at most one active dossier at a consumer (section 8). |
| Publisher | The party that issues a dossier: a manufacturer, a distributor, an extractor or a curator. |
| Consumer | A system that retrieves, validates, stores and uses dossiers. |
| Element | An item of one of the eight element arrays (section 3), with its own `id` and `as_of`. |
| Representation | The public or the restricted form of one dossier version (section 10). |
| View | A named rule pack over elements (section 6). |
| Vocabulary | A closed, versioned list of keys in `vocab/` (section 13.3). |

## 3. Model

A dossier is built from nine primitives. Everything a brochure or data sheet says is expressed with them; there are
no per-topic structures.

| # | Primitive | Where | Holds |
|---|---|---|---|
| 1 | identity | `identity` (one) | Which material this is. |
| 2 | composition | `composition` (zero or one) | What it consists of. |
| 3 | property | `properties[]` | Every single value: a property of something, by some method, under some conditions. |
| 4 | dataset | `datasets[]` | Curves, tables and matrices as numeric or ordinal series. |
| 5 | formulation | `formulations[]` | Starting formulas, test formulas, placebos, comparators. |
| 6 | study | `studies[]` | The protocol frame shared by properties and datasets. |
| 7 | relation | `relations[]` | An interaction with another material or class of materials. |
| 8 | attestation | `attestations[]` | Certificates, declarations, regulatory status. |
| 9 | statement, media | `statements[]`, `media[]` | Display-only text; figures and referenced documents. |

Around them sits the envelope (section 5.1): versions, the source of the dossier and its conformance level.

Variety lives in the **vocabularies**, not in the structure: the set of members is closed, the set of keys grows.
**Views** (section 6) add the typed rules: which members are required for which keys.

## 4. General rules

### 4.1 Encoding and structure

1. A dossier MUST be a single JSON object (RFC 8259), encoded in UTF-8 without a byte order mark.
2. A dossier MUST validate against `schema/dossier.schema.json` (JSON Schema draft 2020-12) and MUST satisfy the
   rules of section 11.
3. The member set is closed at every level. A member that this specification does not define is an error, except
   members whose name matches `x-<domain>:<name>` (section 13.4).
4. A value that is not known MUST be left out. `null`, empty strings, "n/a" and placeholder values MUST NOT be used.

### 4.2 Numbers

1. Numeric data MUST be JSON numbers. The decimal separator is the point; there is no thousands separator, no unit
   and no operator inside a number. `"0,5"`, `"2,500"`, `"< 1"` and `"5 %"` are not numbers.
2. A value that the source states as a limit ("max. 0.1", "up to 5 %", "> 30") MUST be given as a `limit`
   (section 5.5.5). It MUST NOT be turned into an exact value.
3. A value that exists only in a figure MUST be given as `in_figure`. Reading a number off an image is not
   permitted for extracted dossiers (section 7.3) and NOT RECOMMENDED for any other.
4. `as_written` MAY carry the original spelling of a value ("1 400 – 3 300 mPa·s"); it is display-only.

### 4.3 Units

1. Units MUST be UCUM case-sensitive codes (`%`, `mPa.s`, `Cel`, `[pH]`, `mo`, `[CFU]/g`, `1` for dimensionless).
2. Each property key and condition key has a **dimension** in `vocab/property-keys.json` or
   `vocab/condition-keys.json`. `vocab/units.json` gives each dimension its **canonical unit** and the other accepted
   units with their conversion factor. A numeric value whose key has a dimension MUST use the canonical unit or an
   accepted unit of that dimension.
3. Publishers SHOULD use the canonical unit. Consumers MUST convert accepted units to the canonical unit before
   comparing or indexing values, and MUST NOT convert between dimensions (for example kinematic to dynamic
   viscosity).
4. A key without a dimension accepts any syntactically valid UCUM unit; arbitrary instrument units are written as
   UCUM annotations, for example `{arb}`.
5. A percentage that expresses a concentration is % w/w unless the key's definition says otherwise.

### 4.4 Dates

1. `as_of`, `issued` of documents and similar dates use ISO 8601 calendar dates with reduced precision allowed:
   `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. Validity dates (`valid_from`, `valid_until`) MUST be full dates.
   The envelope's `issued` is an RFC 3339 timestamp.
2. **Every element MUST carry `as_of`**: the date on which its content was established or last confirmed by the
   party responsible for it (the study date, the certificate date, the revision date of the source document). It is
   not the date of publication. A publisher MUST NOT stamp old data with the current date unless it has re-confirmed
   the data.

### 4.5 Text

1. Free text is **display-only**. Everything a machine is meant to act on MUST be present in structured members
   (keys, numbers, units, codes). A consumer never needs to parse text to obtain a value.
2. Localized text is an object keyed by BCP 47 language tags. Every localized text MUST contain an entry for the
   envelope's `default_language`.
3. Text members are plain text: no markup, no control characters. Lengths are limited by the schema (200 characters
   for names and labels, 300 for lines, 4000 for statements).

### 4.6 Identifiers and references

1. Every element, composition component and dataset series has an `id` matching `^[a-z][a-z0-9_-]{0,63}$`, unique
   within the dossier.
2. An `id` MUST stay the same across versions of a dossier as long as the element describes the same thing. Consumers
   compare versions by `id`.
3. References are plain `id` strings and MUST resolve inside the same representation (section 10.2).

## 5. Primitives

Member tables list the important members; the schema is complete and authoritative on types and limits.
"R" = required.

### 5.1 Envelope

| Member | R | Meaning |
|---|---|---|
| `standard_version` | R | Version of this specification the dossier follows, `1.<minor>`. |
| `vocab_version` | R | Version of the vocabularies the dossier uses, `1.<minor>`. |
| `dossier_id` | R | `<publisher domain>:<slug>`. Stable across versions; never reused for another material. The domain part MUST equal `source.publisher.domain`. |
| `version` | R | Integer ≥ 1, strictly increasing with every published change. |
| `issued` | R | Timestamp of this version. |
| `supersedes` | R if `version` > 1 | `{version, hash}` of the same representation of the previous version. |
| `representation` | R | `public` or `restricted` (section 10). |
| `restricted_content` | | In a public representation: informative note on what the restricted one adds. |
| `completeness` | R | `full`: the publisher states that the dossier replaces its other documentation for this material. `partial`: it does not. |
| `conformance_level` | R | `L1`, `L2` or `L3` (section 12). |
| `default_language`, `languages` | R / | BCP 47 tags. |
| `declarations` | | `negative_results_included`: results without effect are included. `batch_data_excluded`: no batch data are present. |
| `source` | R | Section 5.2. |

### 5.2 Source

`source.route` records how the dossier came to exist. It decides responsibility (section 7) and precedence
(section 8).

| Route | Publisher | Additional required member |
|---|---|---|
| `manufacturer` | The manufacturer of the material. | — |
| `distributor` | A distributor acting with the manufacturer's authorization. | `authorization`: `manufacturer`, `reference`, `valid_from`; optional `manufacturer_domain`, `valid_until`, `document`. |
| `extracted` | A third party that produced the dossier from documents. | `extraction`: `tool`, `completed`, `sources[]` (media ids of the source documents). |
| `curated` | A curator who entered the content by hand. | `curation`: `method` (`manual` or `migrated_playbook_v1`), `completed`; optional `sources[]`, `reference`. |

`source.publisher` MUST have `name` and `domain`.

### 5.3 Identity

| Member | R | Meaning |
|---|---|---|
| `trade_name` | R | Name of the grade as sold. |
| `product_code` | R for `manufacturer` and `distributor` | The manufacturer's code of this grade. |
| `grade` | | What distinguishes this grade inside its family ("30 % solution", "powder, medium viscosity"). |
| `family` | | Optional grouping; it has no other meaning. |
| `manufacturer` | R | `name`; `domain` and `country` (ISO 3166-1 alpha-2) RECOMMENDED. |
| `inci` | R | INCI names in CosIng spelling, descending by content. `inci_variants[]` gives other regions' names. |
| `cas`, `ec`, `chemical_name`, `synonyms`, `molecular_formula` | | |
| `as_of` | R | |

One dossier describes one grade. Two forms with different use levels (a solution and a powder) are two dossiers,
optionally sharing a `family`.

### 5.4 Composition

`composition.components[]`, each with `id`, `role` (vocabulary `composition-roles`), `inci` or `name`, optional
`cas`, `ec`, `origin` and `content`.

- `content` is exactly one of `exact`, `range`, `limit` or `nominal` (`not_detected`, `present`, `trace`), in % w/w
  of the material as supplied.
- `origin.type` uses vocabulary `origin-types`; `origin.botanical` gives `latin_name`, `plant_part`, `country[]`,
  `extraction_solvent`, `drug_extract_ratio`.
- `complete: true` states that the components describe the whole material.
- Fragrance allergens are components with role `allergen`; marker compounds of extracts with role `marker`.
- The sum of the minimum contents MUST NOT exceed 100 %. When `complete` is true, the sum of the maximum contents
  MUST reach 100 %.
- A restricted component MAY carry `refines: <id of a public component>` to give a more precise content (the exact
  value behind a public range). A refined public component is left out of the sums.

ISO 16128 indexes are properties (`origin.*`, section 6.12), not composition members.

### 5.5 Property

The property is the core primitive: one statement of one value.

```json
{
  "id": "spec-visc", "as_of": "2026-05",
  "key": "rheology.viscosity",
  "basis": "specification",
  "subject": { "kind": "dilution", "medium": "deionized water, neutralized to pH 6.5",
               "material_conc": { "value": 0.5, "unit": "%", "basis": "as_supplied" } },
  "method": { "standard": "iso:2555", "settings": [ { "key": "rotation_speed", "value": 20, "unit": "{rpm}" } ] },
  "conditions": [ { "key": "temperature", "value": 25, "unit": "Cel" } ],
  "value": { "range": { "min": 40000, "max": 60000 } },
  "unit": "mPa.s"
}
```

Required: `id`, `as_of`, `key`, `basis`, `subject`, `value`.

#### 5.5.1 `key`

A key of `vocab/property-keys.json` or an extension key. The key names the property; it never encodes the basis,
the subject, a condition or the analyte. Keys of the form `efficacy.<endpoint>` take their suffix from
`vocab/endpoints.json`.

#### 5.5.2 `basis` (required)

| Value | Meaning |
|---|---|
| `specification` | A release limit guaranteed for every batch. |
| `typical` | A typical value, not guaranteed. |
| `measured` | The result of a specific test or study. |
| `recommended` | The publisher's recommendation for use. |
| `regulatory_limit` | A limit set by a regulator or standard-setting body. Requires `scope.region` and a current `as_of`. |
| `calculated` | Derived by calculation or simulation. |
| `declared` | A declaration without a test behind it. |

The same key can and often does occur with several bases (a recommended use level of 0.5–1 % and a regulatory limit
of 1.1 %). Consumers MUST NOT treat one basis as another.

#### 5.5.3 `subject` (required)

What the value is a property of.

| `kind` | Meaning | Required with it |
|---|---|---|
| `neat` | The material as supplied. | — |
| `dilution` | The material in a simple medium. | `medium`, `material_conc` |
| `formulation` | A formulation of this dossier. | `formulation` (id) |
| `biological_system` | Cells, tissue, organisms exposed to the material. | `system` RECOMMENDED |
| `reference_material` | Another material (a comparator, or a read-across source). | `reference` |

`material_conc` is `{value, unit: "%", basis}` with `basis` one of `as_supplied`, `active`, `total_solids`,
`unspecified`. When a result was obtained on another material and is offered for this one, `read_across_from`
(`name`, `reason`) MUST be present.

#### 5.5.4 `method`, `conditions`

`method` has `standard`, `edition`, `name`, `instrument`, `settings[]` and `non_standard`.

- `standard` is written `<body>:<designation>` in lower case, for example `iso:24444`, `oecd:439`, `ph-eur:2.2.3`.
  The body MUST be listed in `vocab/test-methods.json` (`bodies`); the designation is the standard's own number.
  The registry of designations in that file is not exhaustive.
- `non_standard: true` states explicitly that no published standard was followed.

`conditions[]` and `method.settings[]` are lists of `{key, value + unit | code | text, ref_id}` with keys from
`vocab/condition-keys.json`. A test organism is `{ "key": "organism", "text": "Pseudomonas aeruginosa",
"ref_id": "ATCC 9027" }`.

The same key MAY appear in several properties that differ in `conditions` or `scope`; a conditional value is never
collapsed into one "general" value.

#### 5.5.5 `value` (required, exactly one form)

| Form | Example | Use |
|---|---|---|
| `exact` | `{ "exact": 66.2 }` | A point value. |
| `range` | `{ "range": { "min": 1400, "max": 3300 } }` | Both ends stated together by the source. |
| `limit` | `{ "limit": { "op": "<=", "value": 0.1 } }` | "max.", "up to", "≤", "<", "min.", "≥", ">". `op` is one of `<`, `<=`, `>`, `>=`. |
| `nominal` | `{ "nominal": "not_irritant" }` | A code from the key's nominal set. |
| `text` | `{ "text": { "en": "White to pale yellow powder" } }` | Display-only wording, for keys that allow it. |
| `in_figure` | `{ "in_figure": "fig-3" }` | The value exists only in the referenced figure. |

`unit` is REQUIRED with `exact`, `range` and `limit`. Which forms a key allows, its dimension, its nominal set and
its plausibility bounds are given in `vocab/property-keys.json`.

#### 5.5.6 Other members

| Member | Meaning |
|---|---|
| `comparison` | `vs` (`baseline`, `placebo`, `vehicle`, `untreated`, `benchmark`), `ref` (the comparator formulation or property), `change` (`relative`, `absolute`). |
| `statistics` | `n`, `p` (`{op, value}`), `test`, `significant` (`yes`, `no`, `not_reported`), `dispersion`. |
| `outcome` | `positive`, `no_effect`, `negative`, `inconclusive`. Results without effect are legitimate content and SHOULD be published. |
| `scope` | `region[]` (ISO 3166-1 alpha-2 or a group code of `vocab/regions.json`), `product_type[]` (vocabulary `product-types`). |
| `study` | The study the result belongs to. |
| `analyte` | `{code}`: what the value is the content of, for a key whose term in `vocab/property-keys.json` names a vocabulary in its `analyte` member. `code` is one key of that vocabulary (for `composition.regulated_basis_content`, `vocab/regulated-bases.json`) or an extension key; an extension code is stored with a warning and is not projected. `analyte` is REQUIRED for such a key and MUST NOT appear on any other key. Such a key takes no `scope` or `conditions` (section 6.3); an empty list there counts as absent. A property of an extension key MAY carry it; it is then not interpreted. |

### 5.6 Dataset

A dataset carries a curve, a table or a matrix.

| Member | R | Meaning |
|---|---|---|
| `title` | R | Localized. |
| `axes[]` | R | 2 to 6 axes: `key` (a property key or a condition key), `type` (`numeric`, `ordinal`, `category`), `role` (`independent`, `dependent`), `unit` (numeric axes), `scale` (`lin`, `log`), `legend[]` (ordinal and category axes: `code`, `rank`, `label`). |
| `series[]` | R | `id`, `label`, optional `subject`, `conditions`, and `points`: an array of tuples in axis order. |
| `points_origin` | R | `publisher_raw`: the publisher's own numeric data. `tabulated`: copied from a table of a source document. `none`: only the figure exists. |
| `figure` | R if `points_origin` is `none` | The original figure (media id). RECOMMENDED in every case. |
| `subject`, `basis` | R | As for properties; a series may override `subject`. |
| `method`, `conditions`, `study` | | Shared by all series. |

1. A graph SHOULD be published as numeric series **and** the original figure.
2. A figure without data is allowed. It MUST be marked with `points_origin: "none"`, and its series then have no
   `points`.
3. Ordinal results ("+++", "good / very good", "C / ++ / –") are ordinal axes with a legend; they MUST NOT be
   converted to numbers.
4. An extracted dossier MUST NOT contain points read from an image; its `points_origin` is `tabulated` or `none`.

### 5.7 Formulation

| Member | R | Meaning |
|---|---|---|
| `role` | R | `starting_formula`, `test_formula`, `placebo`, `vehicle`, `benchmark`. |
| `name` | R | Localized. `code` optional. |
| `product_type`, `product_form` | | Vocabularies `product-types`, `product-forms`. |
| `disclosure` | R | `full`: every line with its %. `actives_complete`: every ingredient that contributes to the reported performance is listed with its %. `partial`: anything less. |
| `lines[]` | R | `phase`, `inci`, `trade_name`, `supplier`, `function` (vocabulary `functions`), `percent` or `qs: true`, `is_subject` (this line is the dossier's material). |
| `procedure[]` | | Localized steps, display-only. |

A fully disclosed formulation MUST add up to 100 % (± 0.5) or contain exactly one `qs` line. Measured properties of
a formulation (pH, viscosity, SPF, stability) are properties whose `subject` references it.

### 5.8 Study

`kind` (vocabulary `study-kinds`), `title`, `design` (`control`, `blinding`, `randomized`, `layout`), `subjects`
(`n`, `description`), `duration`, `application[]`, `arms[]` (`role`, `formulation`, `label`), `method`, `lab`
(`type`: `in_house`, `independent`, `not_reported`), `reference` (`citation`, `doi`, `url`), `report` (media id),
`all_endpoints_reported`.

Results are not members of the study; they are properties and datasets that reference it. Consumer perception
studies (self-assessment) are a separate kind and MUST NOT be presented as instrumental measurements. Market
surveys are not studies and do not belong in a dossier.

### 5.9 Relation

`with` (at least one of `class` from vocabulary `interaction-classes`, `inci`, `trade_name`; optional `cas`,
`manufacturer`), `effect` (vocabulary `interaction-effects`), `basis` (`measured`, `declared`, `recommended`),
`rating` (`code`, `rank`, `of`), `conditions[]`, `support[]` (properties, datasets or studies that back it), `text`.

### 5.10 Attestation

| Member | R | Meaning |
|---|---|---|
| `scheme` | R | Vocabulary `attestation-schemes`: certifications, declarations, fragrance standards, regulatory regimes. |
| `status` | R | Vocabulary `attestation-statuses`. |
| `scope` | | `region[]`, `product_type[]`. |
| `issuer`, `certificate_id`, `edition`, `reference` | | `edition` names the edition of the scheme (the IFRA amendment); `reference` an entry in it. |
| `valid_from`, `valid_until` | | Full dates. `issuer` and `valid_until` are REQUIRED with status `certified`. |
| `usage_restriction` | | `codes[]` (vocabulary `usage-restrictions`) and display text. |
| `limits[]` | | `category` with `max` (%) or `prohibited: true`; used for IFRA categories and similar tables. |
| `document` | | Media id of the certificate or statement. |

An attestation states the status of the **raw material**. It never certifies a finished product.

### 5.11 Statement

`kind` (vocabulary `statement-kinds`: description, benefit, claim, guidance, checklist, handling, storage, warning,
disclaimer, mechanism), localized `text`, `supports[]` (the properties, datasets or studies behind a benefit or
claim), `scope`, `source_language`. Statements are display-only (section 14.2). A `claim` without `supports` is an
unsupported claim and MUST be shown as such by consumers that show it.

### 5.12 Media

| Member | R | Meaning |
|---|---|---|
| `kind` | R | `figure`, `structure`, `photo`, `source_document`. |
| `url` | R except for `source_document` | HTTPS. |
| `sha256` | R | Hex SHA-256 of the file. |
| `mime` | R | `image/png`, `image/jpeg`, `image/webp`; `application/pdf` for documents only. Vector and active formats (SVG, HTML) are not allowed. |
| `license` | R | `id` (SPDX identifier, `proprietary` or `unknown`), `holder`, `terms_url`, `redistribution`: `allowed`, `consumer_display` (a consumer may store a copy and show it to its own users) or `none`. |
| `document` | R for `source_document` | `kind` (vocabulary `document-kinds`), `doc_version`, `issued`, `language`, `pages`, `issuer`. |
| `title`, `caption` | | Localized. |

1. Media are referenced, not embedded. Consumers MUST copy media they use to their own storage, verify `sha256`, and
   serve their copy; they MUST NOT hot-link (section 15).
2. Public media of a `manufacturer` or `distributor` dossier MUST have `redistribution` `allowed` or
   `consumer_display`.
3. The safety data sheet is referenced as a `source_document` of kind `sds`; a dossier does not reproduce it.

## 6. Views

A view is a rule pack: the set of keys it covers and the members it requires. A view adds no structure. Views are
identified in `vocab/property-keys.json` (`views`). The rules below are normative and are checked under section 11.

### 6.1 `usage` — the usage view

The usage view is the small, deterministic projection that formulation tools use for dose, phase, pH and
temperature checks. It is defined as a function of the dossier:

A property is **general** when its `basis` is `recommended`, its `subject.kind` is `neat`, and it has neither
`scope` nor `conditions`.

| Output | Source |
|---|---|
| `usage.min`, `usage.max` | The general `use.level`: a `range` gives both; a `limit` with `<=` or `<` gives `max` only; an `exact` gives `min` = `max`. |
| `usage.typical` | The general `use.level_typical` (`exact`). |
| `phase` | Every general `use.phase`: its nominal code is a term of `vocab/process-stages.json`; the term's `usage_view_phase` gives the letter (A water phase, B oil phase, C cool-down, D added to the hot water phase, E added to the hot oil phase). Letters are unique and keep document order. Stages without a letter are not projected. |
| `process` | `"cold"` when a general `use.phase` has a nominal code whose term carries `usage_view_process: "cold"` (in 1.0 the stage `cold_process`); absent otherwise. |
| `ph_window.min`, `ph_window.max` | The general `use.ph_window`: `range`, or `limit` (`>=` gives `min`, `<=` gives `max`). |
| `temperature.max` | The general `use.process_temperature_max`: `exact`, or `limit` with `<=` or `<`. |
| `guidance[]` | The first six statements of kind `guidance` without `scope`, in document order, text of the `default_language`, whitespace collapsed. |
| `checklist[]` | The same for kind `checklist`. |

Rules:

1. A dossier MUST NOT contain more than one general `use.level`. Use levels for a product type, a region or a
   condition carry `scope` or `conditions` and are not part of the usage view.
2. `0 ≤ usage.min ≤ usage.max`, `0 < usage.max ≤ 100`; `usage.typical` lies inside the range.
3. `guidance` and `checklist` texts are limited to 300 characters. A checklist line MUST be a question that can be
   answered from the list of materials of a formula.
4. The usage view is **complete** when it has `usage.max` and either at least one phase letter or
   `process: "cold"`. A material that is only cold-processed therefore reaches L1 without a phase letter.

#### The minimal L1 dossier

A material for which neither a manufacturer nor an extracted dossier exists is represented by a minimal dossier.
It consists of exactly:

- the envelope with `conformance_level: "L1"`, `completeness: "partial"`;
- `source` (normally route `curated`);
- `identity` with `trade_name`, `manufacturer.name`, `inci`, `as_of`;
- the elements of a complete usage view: one general `use.level`, at least one general `use.phase` that maps to a
  letter or to `process: "cold"`, and optionally `use.level_typical`, `use.ph_window`, `use.process_temperature_max`, up to six `guidance`
  and up to six `checklist` statements;
- optionally the source documents as `media` and `evidence` on the elements.

Nothing else is required. `examples/05-minimal-l1-curated.json` is such a dossier.

### 6.2 `profile`

Keys `profile.*`, `solubility.*`, `sensory.descriptor`. Values are nominal codes from closed sets (functions follow
the CosIng function list) or numbers (`profile.hlb`). One property per function, per product application and per
descriptor. This view is what substitution searches match on.

### 6.3 `specification`

All properties with `basis` `specification`. Limits are expected (`limit`, `range`); the test method SHOULD be given.
Typical values MUST use `basis` `typical`, never `specification`.

**`composition.regulated_basis_content`.** The content, in the material as supplied, of a regulated basis: the
element or named substance in which a regulatory limit is expressed ("calculated as F", "(as zinc)",
"corresponding to … % of silver", "(as AgCl)"). It is stated where the basis content cannot be computed from a
defined molecular formula (zeolites, glasses, ferments, silver chloride on titanium dioxide, blends). A basis that
stoichiometry decides ("as acid", "as free base", "as hydrochloride", "H2O2 present or released", "Retinol
Equivalent") has no code; the consumer computes it. Rules:

- `analyte.code` names the basis (section 5.5.6).
- `subject.kind` MUST be `neat`.
- `basis` MUST be one of `specification`, `declared`, `typical`, `measured`.
- `scope` and `conditions` MUST NOT be present. An empty `conditions` list counts as absent (an empty `scope` is
  refused by the schema already).
- The value is `exact`, `range` or `limit`, in a unit of the `mass_fraction` dimension. A source that states the
  content in another dimension (mg/L) gives no value here (section 7.3, "No conversion").

```json
{
  "id": "basis-ag", "as_of": "2026-05",
  "key": "composition.regulated_basis_content",
  "basis": "specification",
  "subject": { "kind": "neat" },
  "analyte": { "code": "element.ag" },
  "value": { "range": { "min": 13.5, "max": 16.5 } },
  "unit": "%"
}
```

#### Reading regulated basis content (non-normative)

- **Code meaning.** An element code (`element.ag`, `element.zn` …) is the total of that element in the material
  as supplied, from all sources. Narrowing to a species ("water-soluble zinc salts", "sulphide") is the job of the
  calculation that applies a given limit, not of the dossier. A substance code (`substance.silver_chloride`) is
  that substance as a phase of the material.
- **Conservative value.** Per material and code, a consumer takes the highest stated value: the value of `exact`,
  `max` of a `range`, the value of a `<=` or `<` limit, and also the value of a `>=` or `>` limit, converted to %
  with the `mass_fraction` factors of `vocab/units.json` and rounded up.
- **Certainty of that value.** From `specification` or `declared`: a bound. From `typical` or `measured`: a
  typical value, used with a warning. From a `>=` or `>` limit: a lower bound; the true content may be higher, so
  the consumer warns. On equal values a bound wins over a typical value, and a typical value over a lower bound.
- **Age.** Values with an older `as_of` are not filtered out; the highest value is kept, which is the conservative
  choice. The age thresholds of section 14.4 (rules 3 and 4) do not make a stated value unusable here: a missing
  or old value leads to a warning, never to a refusal.
- **Units.** Only `mass_fraction` units are read; an extension code is not read.

### 6.4 `efficacy`

Keys `efficacy.<endpoint>` and `consumer.agreement`. Required: `study`; the concentration of the material in the
tested system (`subject.material_conc`, or a formulation with an `is_subject` line that has a percent);
`comparison`; `statistics` (`significant` MAY be `not_reported`); `outcome`. `consumer.agreement` belongs to a
study of kind `consumer_perception`, and such a study reports nothing else.

### 6.5 `interaction`

All relations. `effect` and `with.class` are closed vocabularies. A relation with `basis` `measured` SHOULD list
its `support`.

### 6.6 `uv_performance`

Keys `uv.spf_in_vivo`, `uv.spf_in_vitro`, `uv.spf_calculated`, `uv.uva_pf_in_vivo`, `uv.uva_pf_in_vitro`,
`uv.critical_wavelength`, `uv.uva_uvb_ratio`, `uv.water_resistance_retention`, `uv.spf_boost`, `uv.photostability`.

1. `subject.kind` MUST be `formulation`.
2. The formulation's `disclosure` MUST be `full` or `actives_complete`: every UV filter and every booster with its
   percentage, and the base described (`product_form`).
3. A `starting_formula` or `test_formula` MUST contain the dossier's material (`is_subject` with `percent`).
   Comparator formulations (`placebo`, `vehicle`, `benchmark`) need not.
4. `method.standard` is REQUIRED (ISO 24444, ISO 24442, ISO 24443, ISO 16217, ISO 18861 and the others listed in
   `vocab/test-methods.json`), or `non_standard: true`.
5. `uv.spf_boost` MUST name the comparator formulation in `comparison.ref`. `uv.spf_calculated` MUST have `basis`
   `calculated`.
6. A sunscreen result that cannot satisfy rules 1 to 5 (for example "50 % SPF boost" without a formulation) MUST NOT
   be published as a property. It can only appear as a statement of kind `claim`.

**These values describe the test formulation.** They are not properties of the raw material and say nothing about
any other product. Section 14.3 binds consumers accordingly.

### 6.7 `rheology`

Keys `rheology.*`, as properties and as dataset axes. Required: the `temperature` condition; for
`rheology.viscosity` of a dilution or formulation also `shear_rate` or `rotation_speed` (in `conditions` or
`method.settings`); the concentration and medium through `subject`. In a dataset the required conditions may be
dataset-level, series-level or an axis.

### 6.8 `preservation`

`micro.mic` requires the `organism` condition with the strain number in `ref_id`. `micro.challenge_log_reduction`
and `micro.challenge_result` require `subject.kind` `formulation`.

### 6.9 `safety`

Keys `tox.*`. Required: `method.standard` or `non_standard: true`; the test concentration (`subject.material_conc`)
unless the subject is neat; `read_across_from` when the data come from another material. Conflicting results from
different methods are kept as separate properties; they are not reconciled.

### 6.10 `regulatory`

Attestations of regulatory schemes and properties with `basis` `regulatory_limit`. Required: `scope.region` and an
own `as_of`. These elements state what the publisher reports; they are not legal advice (section 14.4).

### 6.11 `fragrance`

An attestation with scheme `ifra` MUST give the `edition` (amendment) and `limits[]` per category. Allergens are
composition components with role `allergen`.

### 6.12 `sustainability`

Keys `origin.*` and `eco.*`. ISO 16128 indexes and biodegradation values require `method.standard`. The natural
origin index and the natural origin content are different keys; a missing value is left out, it is not zero.

### 6.13 `stability`

Keys `stability.*`. Observations on a formulation reference it as subject and give storage conditions
(`temperature`, `storage_time`, `freeze_thaw_cycles`).

## 7. Provenance

### 7.1 Responsibility

| Route | Who answers for the content | Validation by consumers |
|---|---|---|
| `manufacturer`, `distributor` | The publisher. | Structural only (section 11.1 to 11.3). No evidence is required and none is checked. |
| `extracted` | The extractor answers for faithful extraction, not for the truth of the source. | Structural, plus the deterministic evidence check of section 7.3. |
| `curated` | The curator. | Structural only. Evidence is optional. |

A publisher of route `manufacturer` or `distributor` MAY attach `evidence` to elements (for example a reference to
a study report); consumers treat it as information.

### 7.2 Curated elements

In a dossier of route `extracted` or `curated`, an element MAY carry `curated: true`: it was written by a curator
and is not taken from a source document. Such an element needs no evidence. `curated: true` MUST NOT appear in
dossiers of route `manufacturer` or `distributor`.

### 7.3 Evidence in extracted dossiers

In a dossier of route `extracted`, `identity`, every composition component and every element other than media MUST
carry `evidence[]`, unless it is marked `curated: true`.

```json
"evidence": [
  { "source": "doc-tds", "page": 1, "quote": "Viscosity (20 °C)              25 - 33 mPa·s",
    "supports": ["/value", "/unit", "/conditions"] }
]
```

- `source`: a media element of kind `source_document`. `page`: 1-based page of that document.
- `quote`: verbatim text of that page, at most 400 characters.
- `supports`: JSON Pointers (RFC 6901), relative to the element, of the members this quote proves. A pointer covers
  everything beneath it.

**Coverage.** Every leaf value of the element MUST be covered by at least one evidence entry. Exempt are the members
that are identifiers, references or classification, which a quote cannot prove deterministically: `id`, `as_of`,
`visibility`, `note`, `key`, `basis`, `kind`, `role`, `outcome`, `effect`, `scheme`, `status`, `code`,
`significant`, `as_written`, `disclosure`, `points_origin`, `type`, `scale`, `phase`, `function`, `product_type`,
`product_form`, all references to other elements, and extension members. (The exact list is the constant `EXEMPT`
in `tools/check_dossier.py`.) `analyte` is the exception to this list: its `code` is classification, but the
member is covered explicitly by rule 6. Consumers SHOULD show a human reviewer which members are proven and which
are the extractor's classification.

**Deterministic checks.** A consumer MUST verify, without any model:

1. each `quote` occurs on the stated page of the source document, after normalising Unicode (NFKC), whitespace,
   letter case and end-of-line hyphenation;
2. each covered **number** occurs in at least one of its quotes. A decimal comma is accepted (`0,945` proves
   `0.945`). A token that can be read as a thousands group (`2,500`) proves nothing;
3. each covered **unit** occurs in at least one of its quotes, in a spelling listed in `vocab/units.json`
   (`aliases`); the unit `1` is exempt;
4. each covered **limit operator** is matched by a wording of its direction in a quote ("max", "up to", "≤" for
   `<=`; "min", "at least", "≥" for `>=`; and so on).
5. each covered **identifier** of `identity` (`trade_name`, `product_code`, `grade`, `family.name`, `family.id`,
   `manufacturer.name`, `chemical_name`, `molecular_formula`, and each item of `inci`, `inci_variants[].names`,
   `cas`, `ec` and `synonyms`) and of a composition component (`inci`, `name`, each item of `cas` and `ec`,
   `origin.botanical.latin_name`) occurs in at least one of its quotes, after the same normalisation as in rule 1.
   A quote that is verbatim on the page but names another value proves nothing.
6. a property with `analyte` has at least one evidence entry whose `supports` contains `/analyte` or
   `/analyte/code`, and at least one such quote names the analyte: the term's `symbol` ("Ag", "AgCl") as a whole
   word, case-sensitive, after NFKC normalisation; or one of its `aliases` ("silver") as a whole word, after the
   normalisation of rule 1. A whole word has no letter or digit directly before or after it. An extension code,
   or a code the vocabulary does not hold, needs the covering quote only. Rule 6 proves the name, not the basis: a
   compound line ("Silver chloride: 20 %") names silver too. The number check (rule 2) and the conservative
   reading of section 6.3 cover the rest, since a compound's content stated under an element code overstates the
   element. Ion notation ("Zn2+") is not matched by the symbol, because a digit follows it; such a quote needs an
   alias. A symbol match can be a false positive ("Grade S" names sulfur, "°F" fluorine); it is accepted, because
   the rule guards against an invented analyte, not against a misread one, and the quote is shown to the reviewer.

**No conversion.** An extracted dossier MUST keep the number and the unit of the source. If the source unit is not
an accepted unit of the key, the value is omitted or given as `text`.

**Never from an image.** Values and points that exist only in a figure are `in_figure` and `points_origin: "none"`.

What an extractor left out, and why, is not part of a dossier. It belongs to the import envelope of the system that
handles extraction.

## 8. One dossier per material

### 8.1 Material identity

Two dossiers describe the same material when they name the same manufacturer and the same `product_code`
(compared case-insensitively, ignoring surrounding whitespace). Manufacturers are compared by
`identity.manufacturer.domain` when both dossiers give it, otherwise by the consumer's own manufacturer records.
When a dossier has no `product_code` (possible for `extracted` and `curated`), matching it to a material is a
decision of the consumer and SHOULD involve a person.

### 8.2 Precedence

Sources are ranked:

| Rank | Route |
|---|---|
| 4 (strongest) | `manufacturer` |
| 3 | `distributor` |
| 2 | `extracted` |
| 1 | `curated` |

1. A consumer MUST hold at most one **active** dossier per material.
2. A candidate of a **higher** rank replaces the active dossier.
3. A candidate of a **lower** rank MUST NOT replace the active dossier, whatever its date or version.
4. A candidate of the **same** rank replaces the active dossier only if it has the same `source.publisher.domain`,
   the same `dossier_id` and a greater `version`.
5. Consequently a manufacturer dossier can only be replaced by a newer version of the manufacturer's own dossier.
6. A candidate of the same rank from a different publisher (two distributors, two extractors) MUST NOT replace the
   active dossier automatically; the consumer decides, and SHOULD keep the active one by default.
7. A candidate with the `version` of a dossier the consumer already holds but a different hash MUST be rejected and
   SHOULD raise an alert.
8. When the publisher withdraws the active dossier (section 9.2), the consumer MUST stop presenting it as current
   and MAY activate the strongest remaining candidate.
9. Replacement is of the whole dossier; dossiers are not merged. When an extracted dossier replaces a curated one,
   the extractor or the consumer SHOULD carry curator-written lines over as `curated: true` elements of the new
   dossier. When the new dossier is of route `manufacturer` or `distributor`, curator-written lines cannot be
   carried over (7.2); a consumer keeps them in its own overlay instead (14.5).

The route MUST be stored with the dossier and SHOULD be shown wherever its content is shown.

### 8.3 Distributor authorization

A distributor dossier declares the manufacturer's authorization in `source.authorization`. A consumer SHOULD verify
it against the manufacturer's index (`authorized_publishers`, section 9.2) when the manufacturer publishes one, and
MUST record whether the authorization was verified or only declared. An expired authorization (`valid_until` in the
past) lowers the dossier to the rank of `extracted` for the purpose of rule 8.2.

## 9. Publisher endpoint

### 9.1 Location and domain binding

A publisher serves its index at

```
https://<domain>/.well-known/material-dossier/index.json
```

1. Control of this URL binds the publisher to `<domain>`. `dossier_id` and `source.publisher.domain` of every
   listed dossier MUST carry that domain.
2. A consumer MUST establish the pairing of a manufacturer with a domain once, with a human decision, and MUST
   store it. A dossier for a manufacturer arriving from another domain is not a manufacturer dossier until the
   pairing is re-established.
3. The suffix `material-dossier` is not registered with IANA (RFC 8615) in 1.0; consumers MUST NOT rely on
   registration. Registration may follow in a later version without changing the path.
4. All URLs are HTTPS. Certificate errors are fatal. Redirects away from the publisher's domain and its declared
   `hosts` MUST NOT be followed.

### 9.2 Index

The index validates against `schema/index.schema.json`.

| Member | R | Meaning |
|---|---|---|
| `standard` | R | `"rubedyne-material-dossier"`. |
| `standard_versions` | R | Versions the publisher serves. |
| `publisher` | R | `name`, `domain`, `role` (`manufacturer`, `distributor`, `extractor`, `curator`), optional `country`, `contact`. |
| `updated` | R | Timestamp of the index. |
| `hosts` | | Further hosts that may serve dossiers, signatures and index pages. |
| `keys` | | JWK Set (RFC 7517) for signature verification (section 9.5). |
| `authorized_publishers` | | Manufacturers only: `domain`, `name`, `since`, `until` of authorized distributors. |
| `restricted_access` | | `scheme: "bearer"`, `info_url` (how a partner obtains a token). |
| `dossiers[]` | R | One entry per dossier, see below. |
| `next` | | URL of the next index page. |

Each entry: `dossier_id`, `trade_name`, `product_code`, `version`, `updated`, `status` (`active`, `withdrawn`),
`route`, `conformance_level`, `standard_version`, `vocab_version`, `public` (`url`, `hash`, optional `bytes`,
`signature_url`) and optionally `restricted` (the same members). An active entry MUST have `public`.

A withdrawn dossier stays listed with `status: "withdrawn"` for at least 12 months.

### 9.3 Retrieval

1. `GET <url>` returns the representation as `application/json`. Publishers SHOULD send `ETag` and honour
   conditional requests.
2. The URL of a version SHOULD be immutable (for example `…/exagel-r200/v4.json`); earlier versions SHOULD remain
   retrievable.
3. The restricted representation requires `Authorization: Bearer <token>`. Without a valid token the server answers
   401 (with `WWW-Authenticate: Bearer`) or 403. Tokens MUST NOT be passed in URLs. How a partner obtains a token is
   outside this specification (`restricted_access.info_url`).
4. Consumers SHOULD poll the index no more often than once an hour and fetch only entries whose `version` or `hash`
   changed.

### 9.4 Content hash

The hash of a representation is `sha256:` followed by the lower-case hex SHA-256 of the **exact octets** of the
representation as served (after removing any HTTP content coding). The index states it per representation. A
consumer MUST compute the hash of what it received, compare it with the index, reject a mismatch, and store the
octets or the hash with the dossier. `supersedes.hash` refers to the same representation of the previous version.

### 9.5 Detached signature

Signing is OPTIONAL in 1.0. Version 1.1 is planned to make it REQUIRED for the `manufacturer` route; publishers
are encouraged to sign from the start. When `signature_url` is present, it returns a JWS in compact serialization with a
detached payload (RFC 7515, Appendix F) over the exact octets of the representation, with `alg` `EdDSA` or `ES256`
and a `kid` found in the index's `keys`. A consumer that verifies signatures SHOULD pin the publisher's keys when
the domain pairing is established, and SHOULD treat a key change like a domain change.

## 10. Visibility and representations

1. Every element and every composition component has a `visibility`: `public` (default) or `restricted`.
2. A dossier version has a **public representation** and, optionally, a **restricted representation**. Both carry
   the same `dossier_id` and `version`; `representation` says which one a document is.
3. The public representation MUST NOT contain any element or component with `visibility: "restricted"`.
4. The restricted representation MUST contain every element of the public representation unchanged, plus the
   restricted ones.
5. Within a representation every reference MUST resolve, and a public element MUST NOT reference a restricted one.
   A public representation MAY announce the restricted content in `restricted_content`.
6. Typical restricted content: the exact composition (components with `refines`), full study reports, assay
   specifications of single components.
7. A consumer that holds a restricted representation MUST keep the restricted elements away from users who are not
   entitled to them, and MUST honour `license.redistribution` and `usage_restriction` codes such as
   `partners_only`.

Members that 1.0 treats as restricted by default in guidance to publishers (not by schema): exact contents of a
multi-component material, and source documents of kind `study_report`.

## 11. Validation

A consumer MUST apply, in this order, to every dossier it accepts:

### 11.1 Schema

The dossier validates against the schema of its `standard_version`. A consumer that knows only an older minor
version MUST reject members it does not know (the member set is closed), and SHOULD upgrade.

### 11.2 Vocabulary and values

1. Every vocabulary-controlled member holds a key of its vocabulary at the dossier's `vocab_version`, or an
   extension key. An unknown key without the `x-` form is an error.
2. For each property: the value form is allowed for the key; a nominal code is in the key's nominal set; the unit is
   accepted for the key's dimension; every number, converted to the canonical unit, lies within the key's
   plausibility bounds (`min`, `max`); `range.min ≤ range.max`.
3. Dataset axes: the key is a property key or a condition key; units as above; each point has one value per axis,
   numeric on numeric axes and a legend code on the others.
4. Composition and formulation sums (sections 5.4, 5.7).
5. Every localized text has an entry for `default_language`.

### 11.3 References, visibility, views

1. Ids are unique; references resolve to an element of the right kind.
2. The visibility rules of section 10.
3. The view rules of section 6.
4. Route rules: `curated: true` only where allowed (7.2); `dossier_id` under the publisher's domain; public media of
   publishers are redistributable (5.12).
5. The claimed `conformance_level` does not exceed the level the dossier reaches (section 12).

### 11.4 Evidence

For route `extracted` only: section 7.3.

`tools/check_dossier.py` is a non-normative reference implementation of sections 11.1 to 11.4.

## 12. Conformance levels

A level is a property of a dossier, decided by rule. A publisher claims it in `conformance_level`; the claim MUST
NOT exceed the level reached.

| Level | Requires |
|---|---|
| **L1 — Core** | A valid dossier with `identity` and a complete usage view (section 6.1). |
| **L2 — Technical** | L1, and: `composition` with a content for every component; at least one `profile.function` and `profile.physical_form`; at least three properties with basis `specification` or `typical`; `stability.shelf_life` or `stability.retest_period`; at least one attestation of a regulatory scheme; the SDS referenced as a `source_document`. Graphs may be figures without data, marked as such. |
| **L3 — Complete** | L2, and: no value given as `in_figure`; **every dataset has numeric (or ordinal) series** (`points_origin` is not `none`); every study has `all_endpoints_reported: true`, a `lab`, at least one result, and `subjects.n` for in vivo, consumer and sensory studies; every efficacy result reports `significant` as `yes` or `no`; `declarations.negative_results_included` is true; `completeness` is `full`. |

L3 is the level at which a dossier replaces the brochure. An extracted dossier is `partial` by rule and therefore
never exceeds L2.

## 13. Versioning and extension

### 13.1 Dossier versions

`version` increases by any amount with every published change; a version, once published, MUST NOT change (same
version, same octets, same hash). Element `id`s persist (4.6), so consumers can show a semantic difference between
versions: element added, removed, or changed member by member.

### 13.2 Standard version

`standard_version` is `MAJOR.MINOR`. Within 1.x, a minor version only **adds**: optional members, enumeration
values, views, rules that apply only to new members. It never removes or renames a member, changes a meaning, or
makes an optional member required. Those need 2.0. A dossier valid under 1.n is valid under 1.n+1.

### 13.3 Vocabulary version

`vocab_version` is versioned separately; adding vocabulary keys does not change `standard_version`.

1. Within 1.x, keys are only added. A key is never removed and never changes meaning; it can be marked
   `deprecated` with `replaced_by`.
2. Consumers MUST accept deprecated keys and SHOULD warn.
3. Vocabularies grow by proposal: a publisher uses an extension key (13.4) and proposes it for the next vocabulary
   minor version. Rubedyne, the standard's owner, decides on proposals and issues vocabulary versions. The
   procedure is described in `README.md` ("How the vocabularies grow").
4. External vocabularies are used where they exist: UCUM for units, CosIng for INCI names and functions, ISO, OECD
   and pharmacopoeia designations for methods, ISO 3166-1 for countries, BCP 47 for languages, culture-collection
   numbers for organisms, SPDX for licences.
5. The schemas of a version are served at their `$id` URLs under
   `https://rubedyne.com/schemas/material-dossier/<standard_version>/`. Vocabulary files have no `$id`; each is
   served at the `base` URL of `vocab/index.json` followed by its file name. Consumers SHOULD NOT fetch them at
   validation time; they ship the files of the versions they implement.

### 13.4 Extension keys

`x-<domain>:<name>`, where `<domain>` is a domain the author controls, is allowed

- as a value wherever a vocabulary key is expected (`key`, `conditions[].key`, `scheme`, `nominal`, …), and
- as an additional member on the dossier, on `identity`, on `composition`, on a component and on any element.

Consumers MUST accept and store extension keys and members, MAY display them, and MUST NOT use them in automated
checks, searches by vocabulary, or generated text until the key is part of a vocabulary they implement. A key that
is neither in the vocabulary nor of the `x-` form is an error; this is what catches typing mistakes.

## 14. Consumer rules

### 14.1 Validation and storage

1. A consumer MUST validate (section 11) before it stores or uses a dossier, and MUST apply the precedence rules of
   section 8.
2. A consumer SHOULD store each dossier version whole, with its hash and route, and index properties separately
   (key, canonical-unit bounds, basis, subject concentration, scope) for searching.
3. Structural validation does not make publisher data true. Consumers SHOULD apply the plausibility bounds,
   cross-check against data they already hold (for example a recommended use level above a legal limit they know),
   and present a semantic difference to a person before a new version becomes active.

### 14.2 Free text is display-only

1. Consumers SHOULD NOT feed publisher free text into generative prompts or any other process that could act on
   it. This covers statement texts, `value.text`, procedure steps, captions, labels, notes, method and instrument
   names, legends, and all extension content.
2. Machine use MUST rely on structured members only. Text generated for a model from a dossier is rendered by the
   consumer from keys, numbers, units and codes.
3. The one exception a consumer MAY make is for `guidance` and `checklist` lines of the usage view that a person at
   the consumer has individually approved; by approving them the consumer adopts them as its own content.
4. Wherever free text is shown, it is shown as plain text, with its source.

### 14.3 Claims

1. Results of studies and tests in a dossier describe the tested system: the named formulation, at the stated
   concentration, under the stated conditions. They are the raw-material publisher's data.
2. Sunscreen results (SPF, UVA-PF, critical wavelength, water resistance, SPF boost) describe the **test
   formulation**, not the raw material and not any end product. A consumer MUST NOT turn them into a statement about
   another product, and MUST NOT present them without the formulation they belong to. Commission Recommendation
   2006/647/EC and Regulation (EU) No 655/2013 require that claims for a cosmetic product are substantiated for
   that product.
3. The same holds for efficacy results: a consumer MUST NOT present them as substantiation of a claim for a product
   it helps to formulate. They MAY be shown as "supplier data: X at Y % in Z".
4. Attestations concern the raw material. A consumer MUST honour `usage_restriction`; in particular
   `no_customer_reference` forbids suggesting that a finished product is certified.

### 14.4 Data age and validity

1. Consumers MUST show `as_of` with regulatory elements, and SHOULD show it with every element.
2. An attestation whose `valid_until` has passed is expired: a consumer MUST NOT use it in automated reasoning and
   MUST mark it as expired where it is shown.
3. Consumers SHOULD treat properties with basis `regulatory_limit` and regulatory attestations older than 24 months
   as unconfirmed, and SHOULD NOT use them in automated checks without another source. Regulatory content of a
   dossier is the publisher's report; it is not a compliance source.
4. Consumers SHOULD flag any element older than five years.

### 14.5 Consumer overlay

A consumer MAY keep its own content about a material outside the dossier: checklist questions, guidance lines,
corrections, notes. This overlay:

1. is not part of any dossier, is never published as one and does not change the dossier's hash, route or
   precedence;
2. belongs to the material, not to a dossier version, and therefore survives the replacement of the active
   dossier;
3. MUST be shown as the consumer's content, distinguishable from the publisher's;
4. MAY be merged into the consumer's rendering of the usage view, with overlay lines first, within the limits of
   6.1 rule 3.

Publisher `guidance` and `checklist` lines remain display-only (14.2) until a person at the consumer approves
them one by one; an approved line becomes overlay content.

## 15. Security considerations

- **Untrusted input.** A dossier is input from another organisation, possibly from a compromised endpoint. Schema
  limits (lengths, counts, closed members) bound its size; consumers SHOULD additionally limit the response size
  (5 MB per dossier and 10 MB per index page are reasonable), the request time, and the number of dossiers per
  publisher.
- **Injection through text.** Free text can carry instructions aimed at language models or markup aimed at
  browsers. Section 14.2 and the plain-text rule of 4.5 are the defence; consumers MUST escape text on output and
  MUST NOT render it as HTML or Markdown.
- **Fetching.** A consumer fetches URLs chosen by a third party. It MUST restrict fetches to HTTPS, to the
  publisher's domain and declared `hosts`, refuse private and link-local addresses after DNS resolution, and limit
  redirects (9.1).
- **Media.** Only raster images and PDF are allowed. Consumers MUST verify `sha256`, SHOULD re-encode images, MUST
  NOT execute or inline PDF content, and serve their own copies so that a publisher cannot change or track what
  users see.
- **Domain takeover and replay.** The human-approved domain pairing (9.1), strictly increasing versions, stored
  hashes (8.2 rule 7) and optional signatures (9.5) limit what a taken-over endpoint can do. A semantic difference
  shown to a person before activation (14.1) is the remaining control.
- **Restricted content.** Bearer tokens are secrets; restricted representations MUST be stored and served with
  access control (10.7).
- **Privacy.** A dossier MUST NOT contain personal data of study subjects or of named employees. Contact members
  hold functional addresses.

## 16. References

- RFC 2119, RFC 8174 — requirement key words. RFC 8259 — JSON. RFC 6901 — JSON Pointer. RFC 3339 — timestamps.
  RFC 7515, RFC 7517 — JWS, JWK. RFC 8615 — well-known URIs. BCP 47 — language tags.
- JSON Schema draft 2020-12.
- UCUM — The Unified Code for Units of Measure.
- ISO 3166-1 — country codes. ISO 16128-1/-2 — natural and organic cosmetic ingredients.
- ISO 24444, ISO 24442, ISO 24443, ISO 16217, ISO 18861 — sun protection test methods.
- Regulation (EC) No 1223/2009 on cosmetic products; Commission Regulation (EU) No 655/2013 (common criteria for
  claims); Commission Recommendation 2006/647/EC (efficacy of sunscreen products and the claims made).
- European Commission CosIng database — INCI names and functions.
