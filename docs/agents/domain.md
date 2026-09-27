# Domain docs

This repository uses a single-context layout:

- `CONTEXT.md` at the repository root: domain vocabulary.
- `docs/adr/`: architectural decisions, created as needed.

## Before exploring

Read `CONTEXT.md` and any ADRs relevant to the area being explored.
If either is absent, proceed silently. Use the domain-modeling skill
to record terms or decisions when they are resolved.

## Use domain vocabulary

Use the terms defined in `CONTEXT.md` in issue titles, proposals,
hypotheses, and test names.

If a needed concept is missing, reconsider the terminology or note
the gap for domain-modeling.

## Surface decision conflicts

If a proposal contradicts an existing ADR, identify the ADR and
explain why the decision should be reconsidered.
