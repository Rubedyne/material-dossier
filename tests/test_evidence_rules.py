# SPDX-License-Identifier: Apache-2.0
"""SPEC 7.3 rules 1 to 4 on single quotes: normalisation and hyphenation, how numbers are read (sign, decimal mark,
thousands, the plausible range, the page's decimal mark), unit spellings and limit wordings."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_dossier as cd  # noqa: E402

V = cd.load_vocab(ROOT / "vocab")


# ---- rule 1 ----

@pytest.mark.parametrize("quote, page", [
    ("anti-aging", "for anti-\naging care"),
    ("antiaging", "for anti-\naging care"),
    ("1 - 20 %", "use 1 -\n20 %"),
    ("Does it contain heavy metals? -", "Does it contain heavy metals? -\nDoes it contain"),
    ("pH 5–7", "pH 5−7"),
    ("“natural” origin", '"natural" origin'),
    ("zero width", "zero​ width"),
    ("20 ºC", "20 °C"),
])
def test_quote_on_page(quote, page):
    assert cd.on_page(quote, page)


def test_digits_split_by_a_line_end_hyphen_are_not_joined():
    assert not cd.on_page("120 %", "use 1 -\n20 %")


# ---- rule 2 ----

@pytest.mark.parametrize("quote, expected", [
    ("-5 - 5 °C", [-5, 5]),
    ("Melting range: > -5°C", [-5]),
    ("<-15°C", [-15]),
    ("log Pow -1,06 (22 °C)", [-1.06, 22]),
    ("Optical rotation: −0.01° – +0.01°", [-0.01, 0.01]),
    ("PEG-40", [40]),
    ("5-10 %", [5, 10]),
    ("10 -20 %", [10, 20]),
    ("0,945 g/cm³", [0.945]),
    ("2.5 %", [2.5]),
    ("1,500,000 Da", [1500000]),
    ("1.500.000 Da", [1500000]),
    ("1.234,56", [1234.56]),
    ("1,234.56", [1234.56]),
    ("2.500 mPa·s", [2.5]),   # no range, no page: a point is decimal
    ("2,500 mPa·s", []),      # ... and a comma proves nothing
])
def test_number_readings(quote, expected):
    assert cd.number_readings(quote) == pytest.approx(expected)


def test_groups_of_three_after_a_space_are_one_number_too():
    assert 15000 in cd.number_readings("approx. 15 000 mPa.s")
    assert 1500000 in cd.number_readings("1 500 000 Da")
    assert 3500 in cd.number_readings("LD50 (rat): > 3 500 mg/kg")


def test_the_plausible_range_picks_the_reading():
    ri = cd.plausible_range(V, {"key": "physchem.refractive_index", "unit": "1"})
    assert cd.number_readings("Brechungsindex (20 °C): 1,461 - 1,472", plausible=ri)[-2:] == [1.461, 1.472]
    density = cd.plausible_range(V, {"key": "physchem.density", "unit": "g/cm3"})
    assert cd.number_readings("Dichte 0,998 - 1,012 g/cm³", plausible=density) == [0.998, 1.012]


def test_the_page_decimal_mark_decides_when_the_range_does_not():
    comma_page = "Dichte 0,95 g/cm3\nLD50 > 5.000 mg/kg"
    point_page = "pH 5.5\nLD50 > 2,000 mg/kg"
    assert cd.number_readings("LD50 > 5.000 mg/kg", page=comma_page) == [50, 5000]
    assert cd.number_readings("LD50 > 2,000 mg/kg", page=point_page) == [50, 2000]
    assert cd.number_readings("LD50 > 2,000 mg/kg", page="pH 5.5 and 0,5 %") == [50]  # mixed page
    assert cd.decimal_mark(None) is None


def test_the_range_overrides_the_page():
    ri = cd.plausible_range(V, {"key": "physchem.refractive_index", "unit": "1"})
    assert cd.number_readings("1,461", page="pH 5.5", plausible=ri) == [1.461]


@pytest.mark.parametrize("quote, n", [
    ("Shelf life: TWO years after manufacturing", 2), ("Shelf life : Three years", 3), ("drei Monate", 3),
    ("deux ans", 2), ("két év", 2), ("dodici mesi", 12), ("one year", 1),
])
def test_number_words_prove_their_number(quote, n):
    assert cd.number_in_quote(n, quote)


@pytest.mark.parametrize("quote, n", [
    ("ein Jahr", 1), ("un an", 1), ("egy év", 1), ("due to its structure", 2), ("Sept 2023", 7),
    ("network", 1), ("someone", 1), ("twofold", 2), ("4 hét", 7), ("produit neuf", 9),
])
def test_articles_other_meanings_and_parts_of_words_are_no_number(quote, n):
    assert not cd.number_in_quote(n, quote)


def test_a_key_without_a_range_gives_no_plausible_test():
    assert cd.plausible_range(V, {"key": "use.phase"}) is None


# ---- rules 3 and 4 in the checker ----

def _el(quote, **member):
    return {"id": "p", "evidence": [{"source": "doc", "page": 1, "quote": quote,
                                     "supports": ["/value", "/unit"]}], **member}


def _errors(el):
    R = cd.Report()
    cd.check_evidence("/properties/0(p)", el, V, {"doc": {"kind": "source_document"}}, None, R)
    return R.errors


@pytest.mark.parametrize("unit, quote", [
    ("Cel", "Dissolve at 85℃"), ("Cel", "Kezdeti forráspont 100 ˚C"), ("Cel", "törésmutató 20C° 1,475"),
    ("[CFU]/g", "Total Plate Count ufc/g ≤ 100"), ("mg{KOH}/g", "ACID VALUE <= 0.20 mgKOH/g"),
    ("meq{O2}/kg", "peroxidszám (Meq O2/kg) 2,62"), ("uS/cm", "CONDUCTIVITY TEST <= 300 µS/cm"),
    ("d", "Haltbarkeit: 365 Tage"), ("deg", "Optical Rotation 70 - 100°"),
])
def test_unit_spellings(unit, quote):
    assert not [e for e in _errors(_el(quote, unit=unit, value={"exact": 1})) if "unit" in e]


@pytest.mark.parametrize("unit, quote", [
    ("[CFU]/g", "Total mesophilic aerobic germs MOP-0314 < 100 germs/g"), ("[CFU]/mL", "< 10 germes/ml"),
    ("Cel", "Melting Point: 66-72 C"), ("Cel", "Flashpoint >70 oC (> 158 oF)"), ("Cel", "store below 25C."),
])
def test_unit_spellings_of_draft_7(unit, quote):
    assert not [e for e in _errors(_el(quote, unit=unit, value={"exact": 1})) if "unit" in e]


@pytest.mark.parametrize("quote", ["Vitamin C 10 %", "process at 70", "Protocol 12", "C14-C16 alkyl, 25 %",
                                   "70 cP", "20 Cal"])
def test_a_bare_c_or_oc_is_a_degree_only_directly_after_a_number(quote):
    assert [e for e in _errors(_el(quote, unit="Cel", value={"exact": 1})) if "unit" in e]


def test_the_unit_1_needs_no_covering_quote():
    el = {"id": "p", "unit": "1", "value": {"exact": 1.4},
          "evidence": [{"source": "doc", "page": 1, "quote": "Refractive index 1.4", "supports": ["/value"]}]}
    assert _errors(el) == []


@pytest.mark.parametrize("op, quote", [
    ("<", "Tárolás: 25C° alatt"), ("<=", "höchstens 5 %"), ("<=", "legfeljebb 5 %"), ("<=", "x ＜ 5"),
    ("<=", "temperatures not exceeding 32 °C"), (">", "higher than 80 %"), (">=", "mindestens 2 %"),
])
def test_limit_wordings(op, quote):
    assert cd.has_word(quote, next(w for w in cd.LIMIT_WORDS[op] if cd.has_word(quote, w)))


def test_a_limit_word_stands_alone():
    assert not cd.has_word("10 minutes", "min") and cd.has_word("10 min", "min")
    assert not cd.has_word("ungeöffnet", "unter") and not cd.has_word("Überblick", "über")
