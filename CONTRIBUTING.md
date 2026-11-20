# Contributing to the Rubedyne Material Dossier

The standard is a public draft for feedback: version 1.0, tag `v1.0.0-draft.3`. Comments on the draft and
proposals for new vocabulary keys are welcome through the issue forms of this repository.

## Feedback on the draft

Open an issue with the **Draft feedback** form. Name the SPEC section, say what is unclear or wrong, and suggest
a change if you have one.

## Vocabulary proposals

Open an issue with the **Vocabulary proposal** form when a publisher needs a key that no vocabulary has. Until a
key exists, use a namespaced extension key, `x-<your domain>:<name>` (SPEC 13.4). A proposal names:

- the vocabulary;
- the proposed key and its definition;
- the value forms and, for property keys, the unit dimension;
- one real use: the kind of document the value appears in, with no confidential data;
- the extension key in use, if any.

Rubedyne, the standard's owner, decides on proposals and issues the vocabulary versions (SPEC 13.3 rule 3).
Keys are only added; a key is never removed and never changes meaning.

## Pull requests

Pull requests are not merged. Rubedyne writes every change to the standard itself. If a change comes from an
issue, the CHANGELOG entry credits the proposer by GitHub handle, if the proposer wants that; say so in the issue.

## Licence of contributions

Text submitted in an issue may be used under the repository's licences: CC BY 4.0 for text, and Apache-2.0 for
schema, vocabulary and tool content. See `LICENSE.md`.

## What not to post

Issues are public. Do not post personal data, or confidential data such as an exact composition, an unpublished
study or a customer name.

Security problems in the checker (`tools/check_dossier.py`) or the other tools are not reported in an issue:
write to `info@rubedyne.com`.
