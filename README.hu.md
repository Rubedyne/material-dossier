# Rubedyne Material Dossier — rövid áttekintés

Állapot: **1.0, nyilvános tervezet véleményezésre (tag: v1.0.0-draft.2).**

## Mi ez

Nyílt, géppel olvasható formátum **egy kozmetikai alapanyag** teljes, strukturált dokumentumára. A gyártó
alapanyagonként (eladható fokozatonként) egy JSON-fájlt tesz közzé a saját domainjén; ebben van minden, ami ma a
brosúrában, a TDS-ben és a PDF-mellékletekben áll. A formulázó szoftver közvetlenül ezt olvassa.

## A legfontosabb szabályok

| Kérdés | Válasz a szabványban |
|---|---|
| Mi egy dosszié? | Egy **eladható fokozat/forma**, saját termékkóddal. A termékcsalád csak címke. |
| Hány dosszié lehet egy anyagról? | **Egy.** A forrás rögzítve van, és rangsorolt: gyártó > meghatalmazott forgalmazó > kivonatolt > kurátori. Gyengébb forrás sosem vált le erősebbet; gyártói dossziét csak a gyártó újabb verziója válthat le. |
| Mi lett a v1 material playbookkal? | Beolvadt. A dózis, fázis (A–E), pH-ablak, maximális hőmérséklet és a legfeljebb 6 + 6 guidance/checklist sor a dosszié **használati nézete** (usage view): determinisztikus vetület, amelyet a promptok és a dózis/fázis/pH ellenőrzések továbbra is használnak. |
| Ha egy anyagról semmi más nincs? | **Minimális L1 dosszié:** azonosítás + használati nézet, forrása `curated`. A meglévő jóváhagyott v1 YAML-ek egyszeri szabállyal ilyenné alakíthatók (DESIGN-NOTES 6. fejezet). |
| Ki felel az adatért? | Gyártói és forgalmazói dossziénál a közzétevő: csak szerkezeti ellenőrzés van. Kivonatolt dossziénál minden levélérték mellett `evidence[]` áll (forrásdokumentum, oldal, szó szerinti idézet), amelyet a fogadó oldal determinisztikusan ellenőriz. |
| Nyilvános vagy védett? | Mindkettő. Elemenként `visibility: public / restricted`; egy verziónak két megjelenése van (nyilvános és partneri, tokennel). Tipikusan védett: pontos összetétel, teljes vizsgálati jelentés. |
| Grafikon | Számsor (tengelyek, egységek, módszer, feltételek) **és** az eredeti ábra. Adat nélküli ábra megengedett, de jelölve (`points_origin: none`). Kivonatolt dosszié képről leolvasott pontot nem tartalmazhat. |
| Fényvédő eredmények | SPF, UVA-PF, kritikus hullámhossz, vízállóság, SPF-fokozás csak a **tesztformulához kötve** adható meg (minden szűrő %-kal, alap megnevezve). A szabvány kimondja: ezek a tesztformulát írják le, nem a végterméket, és termék-állítássá nem alakíthatók (2006/647/EK ajánlás, 655/2013/EU rendelet). |
| Szabad szöveg | Csak megjelenítésre. Ami gépi felhasználásra kell, annak strukturált mezőben kell lennie. A fogadó rendszer a gyártói szabad szöveget ne adja generatív promptba; kivétel a használati nézet személy által egyenként jóváhagyott sora. |
| Adat kora | Minden elemen `as_of`; tanúsítványon `valid_until` és használati korlátozás. |
| Megfelelési szintek | **L1** azonosítás + használati nézet · **L2** a TDS tartalma (összetétel, specifikáció, funkció, eltarthatóság, szabályozási státusz, SDS hivatkozva) · **L3** kiváltja a brosúrát (minden grafikon számsorral, minden vizsgálat minden végponttal, a hatástalan eredményekkel együtt). |
| Bővítés | Külön `standard_version` és `vocab_version`; az 1.x csak hozzáad. Saját kulcs: `x-<domain>:<név>`, amelyet a fogadó tárol, de nem értelmez. |

## Szerkezet egy mondatban

Kilenc primitív (identity, composition, property, dataset, formulation, study, relation, attestation,
statement + media), zárt, verziózott szótárak, és ezekre épülő típusos nézetek (szabálycsomagok). A `property`
magja: kötelező `basis` (specifikáció / tipikus / mért / ajánlott / szabályozási határ / számított / nyilatkozott),
kötelező `subject` (mit mértek), és pontosan egy értékforma (pont, tartomány, határ, névleges kód, szöveg, „csak
ábrán”).

## Mi van a mappában

| Fájl | Tartalom |
|---|---|
| `SPEC.md` | A normatív specifikáció (angol, RFC 2119). |
| `schema/` | JSON Schema: dosszié, végpont-index, szótárfájl. |
| `vocab/` | 24 szótárfájl, 895 kulcs (funkciók, végpontok, tulajdonság-kulcsok kanonikus egységgel, módszerek, tanúsítványok …). |
| `examples/` | Hét kitalált dosszié és egy végpont-index; mind átmegy az ellenőrzésen. A 06-os kivonatolt példa egy titán-dioxidra vitt ezüst-kloridé, szabályozott bázis tartalmával. |
| `guides/publisher-guide.md` | Gyakorlati útmutató gyártóknak: brosúra/TDS → dosszié, mezőnként; gyakori hibák; szintenkénti ellenőrzőlista. |
| `tools/check_dossier.py` | Referencia-ellenőrző (nem normatív): séma, szótár, nézet-szabályok, idézet-ellenőrzés, használati nézet, index-hash. |
| `tools/conformance/` | `run_all.py` (minden ellenőrzést lefuttat), `mutation_cases.py` (a megfelelőségi esetek), `rule6_vectors.json` (az evidence 6. szabályának tesztidézetei), `regulated_basis_phrases.json` és a forráslistája (az Annex-báziskifejezések térképe). |
| `tests/` | A futtató tesztjei. |
| `DESIGN-NOTES.md` | Döntések és elvetett alternatívák, eltérések a koncepció-felülvizsgálattól, a v1 playbook migrációs szabálya, nyitott kérdések, az ellenőrzés parancsa és eredménye. |
| `LICENSE-*.txt` | A teljes licencszövegek (CC BY 4.0, Apache-2.0); összefoglaló: `LICENSE.md`. |

## Ellenőrzés

- Mind a hét példa érvényes a sémára (JSON Schema 2020-12, valódi validátorral), minden szótárkulcs létezik, a
  hivatkozások feloldódnak, a nézet-szabályok teljesülnek, a két kivonatolt példa idézetei szó szerint megvannak a
  forrásszövegben.
- 41 szándékosan elrontott változatot az ellenőrző mind elutasít (például SPF tesztformula nélkül, idézetben nem
  szereplő szám, védett elem a nyilvános megjelenésben, bázistartalom `analyte` nélkül), és a 8 elsőbbségi eset a
  szabály szerint dől el.
- A 2026-11-14-i állapot hat példájának használati nézete átment a v1 playbook-validátor szabályain (ez a
  validátor nem része a tárolónak); a migrált v1 playbook és négy további változat oda-vissza azonos eredményt
  adott.

A döntések és a nyitott kérdések: DESIGN-NOTES 8. fejezet és CHANGELOG.

Észrevételt a tervezethez és új szótárkulcsra tett javaslatot a GitHub-tároló issue-űrlapjain lehet beküldeni;
a menetet a `CONTRIBUTING.md` írja le (angolul).
