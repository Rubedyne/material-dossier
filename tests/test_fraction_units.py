# SPDX-License-Identifier: Apache-2.0
"""The `fraction` dimension of vocab/units.json (vocabulary 2026-11-23): an ISO 16128 index is a dimensionless
number from 0 to 1 that documents also give in percent; both units are accepted and a consumer converts to the
canonical unit 1 (SPEC 2.3)."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_dossier as cd  # noqa: E402

V = cd.load_vocab(ROOT / "vocab")
SCHEMA = json.loads((ROOT / "schema" / "dossier.schema.json").read_text())
E1 = json.loads((ROOT / "examples" / "01-humectant-active.json").read_text())
ISO_INDEXES = ["origin.natural_index", "origin.natural_origin_index", "origin.organic_index",
               "origin.organic_origin_index"]


def _errors_of_noi(unit, value):
    d = copy.deepcopy(E1)
    p = next(p for p in d["properties"] if p["id"] == "noi")
    p.update(unit=unit, value=value)
    R, _ = cd.check(d, V, SCHEMA, None)
    return [e for e in R.errors if "(noi)" in e]


def test_the_fraction_dimension_takes_1_and_percent_with_their_factors():
    units = json.loads((ROOT / "vocab" / "units.json").read_text())
    fraction = next(t for t in units["terms"] if t["key"] == "fraction")
    assert fraction["canonical"] == "1" and fraction["units"] == {"1": 1, "%": 0.01}
    dimensionless = next(t for t in units["terms"] if t["key"] == "dimensionless")
    assert dimensionless["units"] == {"1": 1}  # HLB, SPF, refractive index … take no percent


def test_exactly_the_iso_16128_indexes_have_the_fraction_dimension():
    keys = json.loads((ROOT / "vocab" / "property-keys.json").read_text())["terms"]
    assert sorted(t["key"] for t in keys if t.get("dimension") == "fraction") == sorted(ISO_INDEXES)
    for t in keys:
        if t["key"] in ISO_INDEXES:
            assert (t["min"], t["max"]) == (0, 1)


@pytest.mark.parametrize("unit,value", [
    ("%", {"exact": 58.3}), ("%", {"range": {"min": 95, "max": 100}}), ("%", {"exact": 0}),
    ("1", {"exact": 0.99}), ("1", {"exact": 1}),
])
def test_an_index_in_percent_or_in_1_is_valid(unit, value):
    assert _errors_of_noi(unit, value) == []


@pytest.mark.parametrize("unit,value,expect", [
    ("%", {"exact": 158}, "plausible"), ("1", {"exact": 58.3}, "plausible"),
    ("[ppm]", {"exact": 1}, "not accepted"),
])
def test_an_index_out_of_range_after_conversion_or_in_another_unit_is_refused(unit, value, expect):
    errors = _errors_of_noi(unit, value)
    assert errors and expect in errors[0]
