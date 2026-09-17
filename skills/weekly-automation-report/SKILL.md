---
name: weekly-automation-report
description: Aggregate validated automation data across a weekly reporting window and produce a consistent trend, outcome, risk, and follow-up report. Use when a workflow needs a weekly summary without recomputing from uncontrolled copies or caches.
---

# Weekly automation report

Create a weekly report from validated daily or event-level data. The skill is platform-neutral and can be used for engineering jobs, data pipelines, content operations, or business automation.

## Inputs

Accept:

- an explicit week start and end, timezone, and reporting convention;
- daily summaries or event-level records;
- totals, stage funnels, failure categories, recovery actions, and ownership data;
- optional comparison period.

Use the same metric definitions throughout the report. Prefer event-level data when daily summaries cannot be reconciled.

## Workflow

1. Confirm the exact reporting window and whether the week is Monday–Sunday or another convention.
2. Validate that each included day belongs to the window.
3. Reconcile weekly totals against daily totals and identify missing days.
4. Describe trends only when the data supports them; avoid causal claims from counts alone.
5. Group failures by stage and distinguish repeat incidents from isolated events.
6. Produce concise follow-up actions with owners or unresolved ownership.

## Output

Return:

- period and data completeness;
- weekly status;
- total throughput and stage funnel;
- day-by-day highlights or trend table;
- failure, risk, and recovery summary;
- comparison with the previous period when supplied;
- next actions and open questions.

Do not expose credentials, raw logs, private URLs, or unredacted personal data. Do not turn missing data into zero.

## Boundaries

- Read and aggregate only.
- Do not mutate source records or send notifications unless explicitly requested by the caller.
- Mark incomplete or contradictory metrics clearly.
