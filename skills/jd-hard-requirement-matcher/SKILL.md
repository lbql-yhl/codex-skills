---
name: jd-hard-requirement-matcher
description: Evaluate a candidate or record against explicit, lawful, job-relevant hard requirements and return an evidence-based pass/fail decision. Use when a workflow needs deterministic requirement matching without relying on keyword similarity or hidden criteria.
---

# JD hard-requirement matcher

Use this skill to compare structured requirements with candidate or entity evidence. The skill is intentionally platform-neutral: it does not assume a browser, database, CRM, ATS, or messaging service.

## Inputs

Accept either structured JSON or an equivalent table containing:

- `subject`: the candidate/entity being evaluated;
- `requirements`: explicit hard requirements, each with an `id`, `text`, and optional `evidence_policy`;
- `evidence`: direct observations or source excerpts, each tied to a requirement when possible;
- optional `context`: job title, source, timestamp, and record identifiers.

Only use requirements supplied by the user or the calling workflow. Use lawful, job-relevant criteria and do not infer protected characteristics or invent thresholds.

## Decision rules

1. Evaluate every hard requirement independently.
2. Direct evidence must support the requirement; keyword overlap alone is not evidence.
3. Missing, ambiguous, negated, stale, or contradictory evidence does not satisfy a hard requirement.
4. Stop deep analysis after a clearly failed hard requirement, but retain the reason and evidence used.
5. Do not compensate for a failed hard requirement with unrelated strengths.
6. Keep the output concise and do not reproduce an entire resume or source record.

## Output

Return a compact result with:

- `decision`: `PASS`, `FAIL`, or `NEEDS_REVIEW`;
- `requirement_results`: one result per requirement with `status`, `evidence`, and `reason`;
- `matched_strengths`: only when relevant;
- `risks_or_missing_evidence`;
- `subject_ref` and `context_ref` when supplied.

`PASS` requires every hard requirement to pass. Use `NEEDS_REVIEW` only when the workflow explicitly allows human review for unresolved evidence; otherwise treat unresolved evidence as `FAIL`.

## Boundaries

- Do not contact, message, forward, reject, or mutate the source system.
- Do not persist data unless the calling workflow explicitly provides a storage contract.
- Do not expose sensitive source text beyond the minimum evidence needed for the decision.
