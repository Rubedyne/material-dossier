# SPDX-License-Identifier: Apache-2.0
"""Test of the GitHub issue forms in .github/ISSUE_TEMPLATE: they load, they have the fields GitHub requires,
and the vocabulary dropdown lists exactly the vocabularies of vocab/index.json."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FORMS = ROOT / ".github" / "ISSUE_TEMPLATE"
TYPES = {"markdown", "input", "textarea", "dropdown"}
LABELS = {"vocabulary-proposal.yml": "vocabulary-proposal", "draft-feedback.yml": "draft-feedback"}


def load(name):
    with open(FORMS / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_issue_forms():
    # Every template loads.
    names = sorted(p.name for p in FORMS.glob("*.yml"))
    assert names == ["config.yml", "draft-feedback.yml", "vocabulary-proposal.yml"]
    loaded = {name: load(name) for name in names}
    for name, data in loaded.items():
        assert isinstance(data, dict), name

    # The two forms have name, description, labels and a well-formed body.
    for name, label in LABELS.items():
        form = loaded[name]
        for key in ("name", "description"):
            assert isinstance(form.get(key), str) and form[key].strip(), (name, key)
        assert form.get("labels") == [label], name
        body = form.get("body")
        assert isinstance(body, list) and body, name
        ids = []
        for item in body:
            assert item.get("type") in TYPES, (name, item)
            if item["type"] == "markdown":
                assert item.get("attributes", {}).get("value"), (name, item)
                continue
            assert isinstance(item.get("id"), str) and item["id"], (name, item)
            assert isinstance(item.get("attributes", {}).get("label"), str), (name, item)
            ids.append(item["id"])
        assert len(ids) == len(set(ids)), name

    # The vocabulary dropdown lists the vocabularies of vocab/index.json, in order.
    index = json.loads((ROOT / "vocab" / "index.json").read_text(encoding="utf-8"))
    expected = [v["vocab"] for v in index["vocabularies"]]
    body = loaded["vocabulary-proposal.yml"]["body"]
    dropdowns = [i for i in body if i["type"] == "dropdown" and i["id"] == "vocabulary"]
    assert len(dropdowns) == 1
    options = dropdowns[0]["attributes"]["options"]
    assert all(isinstance(o, str) for o in options)
    assert options == expected and len(options) == 24

    # No blank issues; one contact link to the landing page.
    config = loaded["config.yml"]
    assert config["blank_issues_enabled"] is False
    links = config["contact_links"]
    assert len(links) == 1
    assert links[0]["name"] == "Rubedyne Material Dossier"
    assert links[0]["url"] == "https://rubedyne.com/material-dossier"
    assert isinstance(links[0].get("about"), str) and links[0]["about"].strip()
