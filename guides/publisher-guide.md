# Publisher guide

For raw-material manufacturers (and their authorized distributors) who want to publish Material Dossiers.
This guide is practical; where it and `SPEC.md` differ, `SPEC.md` is right.

All examples here are invented.

## 1. What you publish

One JSON file per **sellable grade**: each product code gets its own dossier. A solution and a powder of the same
active, or three viscosity grades of one polymer, are separate dossiers; put the family name in `identity.family`.

You publish it on your own domain, list it in an index file, and update it by issuing a new version. Software at
your customers reads it. You are responsible for the content; consumers check the structure, not the truth.

You can start small. Level 1 needs only the identity and the use data of the material. Level 2 is the content of a
technical data sheet. Level 3 replaces the brochure, with the numbers behind every graph.

## 2. The skeleton

```json
{
  "standard_version": "1.0",
  "vocab_version": "1.0",
  "dossier_id": "example.com:exagel-r200",
  "version": 1,
  "issued": "2026-11-02T09:00:00Z",
  "representation": "public",
  "completeness": "partial",
  "conformance_level": "L1",
  "default_language": "en",
  "source": { "route": "manufacturer", "publisher": { "name": "Example Ingredients Ltd.", "domain": "example.com" } },
  "identity": { "trade_name": "Exagel R200", "product_code": "EX-2200",
                "manufacturer": { "name": "Example Ingredients Ltd.", "domain": "example.com", "country": "IE" },
                "inci": ["Acrylates/C10-30 Alkyl Acrylate Crosspolymer"], "as_of": "2026-05" },
  "properties": [], "statements": []
}
```

The skeleton becomes a valid Level 1 dossier once the use data of section 3.4 are added.

- `dossier_id` is your domain, a colon and a name you choose. It never changes and is never reused.
- `version` goes up with every change you publish. From version 2 on, `supersedes` names the previous version and
  its hash.
- Every element you add needs an `id` (your choice, stable across versions) and an `as_of` date: when the data were
  established, not when you typed them.

## 3. From brochure to dossier, section by section

### 3.1 Header of the data sheet → `identity`

| On the data sheet | In the dossier |
|---|---|
| Trade name | `identity.trade_name` |
| Product number | `identity.product_code` |
| "Powder grade", "30 % solution" | `identity.grade` |
| INCI name(s) | `identity.inci[]`, CosIng spelling, descending by content. US or China names: `inci_variants[]` |
| CAS, EC numbers | `identity.cas[]`, `identity.ec[]` (and per component in `composition`) |
| Chemical name, formula | `chemical_name`, `molecular_formula` |
| Structural formula drawing | a `media` element of kind `structure` |

### 3.2 Composition statement → `composition`

One component per INCI name, with a `role` and a `content`.

```json
{ "id": "c-betaine", "inci": "Betaine", "cas": ["107-43-7"], "role": "active",
  "content": { "range": { "min": 12, "max": 16 } },
  "origin": { "type": "plant", "botanical": { "latin_name": "Beta vulgaris", "plant_part": "root" } } }
```

- "28.5–32.0 %" is a `range`; "max. 0.1 %" is `{ "limit": { "op": "<=", "value": 0.1 } }`; "n.d." in an allergen
  table is `{ "nominal": "not_detected" }`.
- Preservatives, antioxidants, solvents and carriers are components too (`role`).
- If you do not want the exact composition public, publish ranges publicly and the exact values in the restricted
  representation (section 6).
- Plant origin, plant part, country, extraction solvent and drug–extract ratio go into `origin.botanical`.
- ISO 16128 indexes are properties (3.9), not part of the composition.

### 3.3 Specification and typical data → `properties`

Each row of the table is one property.

| On the data sheet | `key` | `basis` | `value`, `unit` |
|---|---|---|---|
| Appearance: white powder | `physchem.appearance` | `specification` | `{ "text": { "en": "White powder" } }` |
| pH (10 % in water, 20 °C): 5.0–6.5 | `physchem.ph` | `specification` | `range` 5.0–6.5, `[pH]`; subject = dilution 10 % in water; condition temperature 20 `Cel` |
| Viscosity (0.5 %, 20 rpm, 25 °C): 40 000–60 000 mPa·s | `rheology.viscosity` | `specification` | `range`, `mPa.s`; subject = dilution; `method.settings` rotation speed; condition temperature |
| Acid value: max. 0.1 mg KOH/g | `physchem.acid_value` | `specification` | `limit` `<=` 0.1, `mg{KOH}/g` |
| Lead: < 1 ppm | `purity.lead` | `specification` | `limit` `<` 1, `[ppm]` |
| Total viable count: < 100 cfu/g | `micro.total_aerobic_count` | `specification` | `limit` `<` 100, `[CFU]/g` |
| Density (20 °C): approx. 1.12 g/cm³ — "typical, not part of the specification" | `physchem.density` | `typical` | `exact` 1.12, `g/cm3` |
| Shelf life: 24 months | `stability.shelf_life` | `specification` | `exact` 24, `mo` |

Three members matter most:

- **`basis`** says in what sense the number holds: `specification` (guaranteed), `typical`, `measured` (one test),
  `recommended` (your advice), `regulatory_limit`, `calculated`, `declared`.
- **`subject`** says what was measured: the material as supplied (`neat`), a dilution (medium and concentration), a
  formulation of this dossier, a biological system, or another material.
- **`value`** has exactly one form. Use `limit` for "max.", "min.", "<", ">", "up to". Never write a limit as an
  exact number.

Put the measuring conditions where they belong: the standard in `method.standard` (`iso:2555`, `ph-eur:2.2.3`),
the instrument and its settings in `method`, temperature and the like in `conditions`. A footnote such as "all
viscosities measured at 25 °C, 20 rpm" has to be repeated on every property it applies to.

### 3.4 "Use" paragraph → the usage view

This is the part formulation software checks formulas against. It is also all that Level 1 needs.

| On the data sheet | In the dossier |
|---|---|
| "Recommended use level 1–5 %" | `use.level`, basis `recommended`, subject `neat`, `range` 1–5, `%` |
| "up to 5 %" | the same with `{ "limit": { "op": "<=", "value": 5 } }` |
| "typically 3 %" | `use.level_typical`, `exact` 3 |
| "2–8 % in rinse-off products" | a second `use.level` with `scope.product_type: ["rinse_off"]` |
| "add to the water phase" / "oil phase" / "below 40 °C at the end" | `use.phase` with `water_phase` / `oil_phase` / `cool_down`; one property per allowed stage |
| "for formulations of pH 4–8" | `use.ph_window`, `range` 4–8, `[pH]` |
| "do not heat above 60 °C" | `use.process_temperature_max`, `limit` `<=` 60, `Cel` |
| "EU: max. 10 %" | `use.level`, basis `regulatory_limit`, `scope.region: ["EU"]`, with its own `as_of` |
| Processing advice in sentences | `statements` of kind `guidance` (at most 300 characters each; the first six count) |
| Questions a reviewer should ask of a formula | `statements` of kind `checklist` ("Is a neutralizer present?") |

Only one use level may be "general" (no scope, no conditions). Everything specific to a product type, a region or a
condition gets a `scope` or `conditions`.

### 3.5 Functions, form, solubility, HLB, sensory → `profile`

One property each, with a code from the vocabulary:

```json
{ "id": "fn-humectant", "as_of": "2026-03", "key": "profile.function", "basis": "declared",
  "subject": { "kind": "neat" }, "value": { "nominal": "humectant" } }
```

`profile.function` (CosIng function names), `profile.application` (product types), `profile.physical_form`,
`profile.ionic_character`, `profile.hlb`, `profile.required_hlb`, `solubility.water`, `solubility.oil`,
`sensory.descriptor`. Marketing adjectives that have no code stay in a `benefit` statement.

### 3.6 Graphs → `datasets`

Publish the numbers behind the graph and the picture.

```json
{ "id": "ds-visc-conc", "as_of": "2026-05", "title": { "en": "Viscosity against polymer concentration" },
  "basis": "typical", "points_origin": "publisher_raw", "figure": "fig-visc-conc",
  "subject": { "kind": "dilution", "medium": "deionized water, neutralized to pH 6.5" },
  "method": { "standard": "iso:2555", "settings": [ { "key": "rotation_speed", "value": 20, "unit": "{rpm}" } ] },
  "conditions": [ { "key": "temperature", "value": 25, "unit": "Cel" } ],
  "axes": [ { "key": "material_concentration", "type": "numeric", "unit": "%", "scale": "lin", "role": "independent" },
            { "key": "rheology.viscosity", "type": "numeric", "unit": "mPa.s", "scale": "log", "role": "dependent" } ],
  "series": [ { "id": "ser-conc", "label": { "en": "Exagel R200" },
                "points": [[0.1, 1200], [0.2, 9500], [0.5, 51000], [1.0, 79000]] } ] }
```

- Several curves in one graph are several `series`, each with the condition that distinguishes it.
- Tables with "+", "++", "good / very good" are datasets with an ordinal axis and a `legend`; do not turn them into
  numbers.
- If you only have the picture, publish it with `points_origin: "none"`. That is allowed up to Level 2. Level 3
  needs the numbers.

### 3.7 Studies → `studies`, `formulations`, `properties`

1. Describe the **study** once: kind (`in_vivo`, `ex_vivo`, `in_vitro`, `in_silico`, `consumer_perception`,
   `sensory_panel`, …), design, number of subjects, duration, application, laboratory.
2. Describe each **arm** as a formulation (test formula, placebo, benchmark) with all lines and percentages. Mark
   your material's line with `is_subject: true`.
3. Give each **result** as a property that references the study and the formulation:

```json
{ "id": "eff-hydration", "as_of": "2024-02", "key": "efficacy.hydration", "basis": "measured",
  "subject": { "kind": "formulation", "formulation": "f-test" }, "study": "st-hydration",
  "method": { "name": "Corneometry", "non_standard": true },
  "conditions": [ { "key": "time_point", "value": 672, "unit": "h" } ],
  "value": { "exact": 24.1 }, "unit": "%",
  "comparison": { "vs": "placebo", "ref": "f-placebo", "change": "relative" },
  "statistics": { "n": 24, "p": { "op": "<", "value": 0.01 }, "significant": "yes" },
  "outcome": "positive" }
```

- **Publish the results without effect too** (`outcome: "no_effect"`, `significant: "no"`). They are what makes the
  positive ones credible, and Level 3 requires that you state all endpoints are reported.
- Self-assessment questionnaires ("87 % agreed that…") are a `consumer_perception` study with `consumer.agreement`
  results. Do not mix them with instrumental results. Market research ("72 % of consumers want…") is not a study
  and does not belong in a dossier.
- A result obtained on a sister product needs `read_across_from`.

### 3.8 Sunscreen data

SPF, UVA-PF, critical wavelength, water resistance and SPF boost are results of a **test formulation**, never of
the filter or booster itself. The rules are strict:

- the property's subject is the formulation;
- the formulation lists every UV filter and booster with its percentage and names the base (`product_form`);
- the method standard is given (`iso:24444`, `iso:24443`, …);
- an SPF boost names the comparator formulation.

"Boosts SPF by 50 %" without the formulation cannot be published as a value. It can only be a `claim` statement,
and consumers will show it as an unsupported claim.

Add a disclaimer statement that these results do not transfer to other products. Your customers still need their
own tests for their own product (Recommendation 2006/647/EC, Regulation (EU) No 655/2013).

### 3.9 Compatibility → `relations`

```json
{ "id": "rel-cationic", "as_of": "2026-05", "with": { "class": "cationic_surfactants" },
  "effect": "incompatible", "basis": "declared" }
```

Name the partner by class (vocabulary `interaction-classes`) or by INCI. Give the condition when there is one
("above 0.5 % sodium chloride"). If you measured it, point to the property or dataset in `support`.

### 3.10 Safety data → `properties` with `tox.*`, and the SDS as a document

Selected values only: acute toxicity, irritation, sensitisation, phototoxicity, mutagenicity, HRIPT. Each with the
guideline (`oecd:439`) and the test concentration. Do not copy the SDS; reference it as a `media` element of kind
`source_document` with document kind `sds`. Leave "no data available" rows out.

### 3.11 Regulatory status, certificates, declarations → `attestations`

| Document | In the dossier |
|---|---|
| "Listed in IECIC 2021" | scheme `cn_iecic`, status `listed`, `scope.region: ["CN"]`, `edition` |
| REACH registered | scheme `eu_reach`, status `registered` |
| COSMOS approval, valid for one year | scheme `cosmos`, status `approved`, `issuer`, `certificate_id`, `valid_from`, `valid_until`, `usage_restriction` |
| Vegan, GMO-free, BSE/TSE, CMR declarations | one attestation each (`vegan`, `gmo_free`, `bse_tse_free`, `cmr_free`), status `compliant` or `free_of` |
| IFRA certificate | scheme `ifra`, `edition` (the amendment), `limits[]` per category with `max` or `prohibited` |
| ISO 16128 letter | attestation `iso_16128` plus properties `origin.natural_origin_index` etc. with `method.standard: "iso:16128-2"` |

Always give `valid_until` for certificates, and say in `usage_restriction` what your customer may not do with the
certificate (for example `no_customer_reference`).

### 3.12 Starting formulations → `formulations`

Role `starting_formula`, all lines with phase, INCI, percent (one line may be `qs`), your material marked
`is_subject`, the procedure as steps. Measured data of the formulation (pH, viscosity, stability, SPF) are
properties with the formulation as subject.

### 3.13 Descriptions, benefits, claims → `statements`

Free text is for people. Software that consumes dossiers shows it and does not act on it. So: whatever you want
formulation software to use must also be present as a property, relation or attestation. A `claim` should point to
the results behind it in `supports`.

## 4. Numbers and units

- JSON numbers with a decimal **point**. No thousands separators, no units, no "<" inside the number.
- Units are UCUM codes: `%`, `[ppm]`, `mPa.s`, `Cel`, `[pH]`, `mo`, `g/cm3`, `[CFU]/g`, `nm`, `1` (no unit).
  Each key lists its accepted units in `vocab/property-keys.json` and `vocab/units.json`; prefer the canonical one.
- Keep the original wording in `as_written` if you like ("40 000 – 60 000 mPa·s").
- Dates: `2026`, `2026-05` or `2026-05-17`.

## 5. Publishing

1. Put each dossier on your web server over HTTPS, at a URL that does not change for that version, for example
   `https://example.com/material-dossier/exagel-r200/v1.json`.
2. Compute its SHA-256 (`sha256sum v1.json`).
3. List it in `https://example.com/.well-known/material-dossier/index.json`:

```json
{ "standard": "rubedyne-material-dossier", "standard_versions": ["1.0"],
  "publisher": { "name": "Example Ingredients Ltd.", "domain": "example.com", "role": "manufacturer" },
  "updated": "2026-11-02T09:00:00Z",
  "dossiers": [ { "dossier_id": "example.com:exagel-r200", "trade_name": "Exagel R200", "product_code": "EX-2200",
                  "version": 1, "updated": "2026-11-02T09:00:00Z", "status": "active", "route": "manufacturer",
                  "conformance_level": "L3", "standard_version": "1.0", "vocab_version": "1.0",
                  "public": { "url": "https://example.com/material-dossier/exagel-r200/v1.json",
                              "hash": "sha256:…" } } ] }
```

4. To change something: issue version 2 as a new file, update the index entry. Never edit a published version.
5. To retire a grade: set `status: "withdrawn"` and keep the entry for a year.
6. Figures: PNG, JPEG or WebP at stable URLs, with their SHA-256 and a licence that lets consumers store and show
   them (`redistribution: "consumer_display"` at least). No SVG.
7. If distributors publish your dossiers, list their domains in `authorized_publishers`.

## 6. Public and restricted content

Mark anything you only share with partners with `visibility: "restricted"`. You then serve two files per version:

- the **public** one, without any restricted element;
- the **restricted** one, with everything, behind `Authorization: Bearer <token>`.

Typical: public composition in ranges, exact composition restricted (`refines`); public study summary as
properties, full report restricted. A public element must not point to a restricted one.

## 7. Common mistakes

| Mistake | Instead |
|---|---|
| `"value": { "exact": 5 }` for "up to 5 %" | `limit` with `<=` |
| A regulatory maximum published as the recommended use level | separate properties with different `basis` |
| Typical data labelled `specification` | `basis: "typical"` |
| Viscosity without concentration, medium, temperature or speed | `subject` as dilution, `conditions`, `method.settings` |
| One "general" value where the source gives several by product type or pH | several properties with `scope` or `conditions` |
| SPF published against the raw material | tie it to the test formulation |
| Concentration without saying of what | `material_conc.basis`: `as_supplied`, `active` or `total_solids` |
| Numbers read off your own graph by eye | publish the raw series, or mark the figure as having no data |
| Only the positive endpoints of a study | all endpoints, with `outcome` |
| Certificate without validity | `valid_from`, `valid_until` |
| Today's date as `as_of` on five-year-old test data | the date of the test |
| Batch values from a certificate of analysis | leave them out; a dossier is not batch data |
| A key that does not exist, slightly misspelled | check `vocab/`; for a genuinely new key use `x-yourdomain.com:name` and propose it |
| Text in a number field (`"n/a"`, `"-"`) | leave the element out |
| Instructions or links in free text | plain sentences; consumers strip and escape them anyway |
| Editing a published version | new `version` |

## 8. Conformance checklist

Run `.venv/bin/python tools/check_dossier.py path/to/your-dossier.json` from the repository root (setup: README,
"Checking a dossier"); it reports the level your dossier reaches and what is missing for the next one.

### Level 1 — Core

- [ ] Valid against the schema; all keys in the vocabularies.
- [ ] `identity`: trade name, product code, manufacturer, INCI.
- [ ] One general recommended `use.level` with an upper bound.
- [ ] At least one `use.phase` (water phase, oil phase, cool-down, added to the hot water phase, added to the hot
      oil phase), or `cold_process` for a material that is processed only without heating.
- [ ] Recommended: `use.level_typical`, `use.ph_window`, `use.process_temperature_max`, a few `guidance` lines.
- [ ] Every element has `id` and `as_of`.
- [ ] Listed in your index with its hash.

### Level 2 — Technical (the data sheet)

- [ ] Level 1.
- [ ] `composition`: every component with role and content.
- [ ] At least one `profile.function` and the `profile.physical_form`.
- [ ] The specification: at least three properties with basis `specification` or `typical` (in practice: all rows
      of your specification table).
- [ ] `stability.shelf_life` or `stability.retest_period`.
- [ ] Regulatory status for at least one region as an attestation.
- [ ] The SDS referenced as a source document.
- [ ] Certificates with validity dates and usage restrictions.
- [ ] Graphs present at least as figures, marked `points_origin: "none"` when without data.

### Level 3 — Complete (replaces the brochure)

- [ ] Level 2.
- [ ] Every graph has its numeric (or ordinal) series.
- [ ] No value exists only in a figure.
- [ ] Every study: laboratory, number of subjects, at least one structured result, `all_endpoints_reported: true`.
- [ ] Every efficacy result states whether it was significant.
- [ ] `declarations.negative_results_included: true`.
- [ ] `completeness: "full"`.
- [ ] Sunscreen and efficacy results tied to fully described test formulations.
