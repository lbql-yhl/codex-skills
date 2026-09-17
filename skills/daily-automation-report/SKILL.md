---
name: daily-automation-report
description: Build a concise, consistent daily report from structured automation run data, including status, throughput, failures, risks, and next actions. Use when a workflow needs a human-readable daily summary without reopening or mutating the source system.
---

# Daily automation report

Generate a daily report from the data supplied by the calling workflow. Keep the report independent from any specific CRM, browser, database, chat system, or notification provider.

## Inputs

Prefer a structured object containing:

- reporting date and timezone;
- run events or an already validated run summary;
- counts for processed, successful, failed, skipped, and blocked items;
- item-level or stage-level breakdowns when available;
- risk, recovery, and data-quality notes;
- optional output and notification destinations.

Use one source-of-truth dataset for all totals. If two totals disagree, surface the discrepancy instead of silently choosing a number.

## Workflow

1. Establish the reporting window and timezone.
2. Validate that event timestamps and counters fall inside the window.
3. Reconcile global totals with stage or item-level totals where possible.
4. Separate business outcomes from infrastructure failures and blocked work.
5. Summarize meaningful risks, recoveries, and follow-up actions.
6. Render the requested output format only after validation.

## Output

Include:

- report title and period;
- overall status: `SUCCESS`, `PARTIAL`, `BLOCKED`, or `FAILED`;
- key totals and funnel stages;
- notable successes;
- failures, risks, and data-quality exceptions;
- next actions or owner handoffs;
- source timestamp or run reference when supplied.

Do not expose secrets, tokens, credentials, raw tracebacks, private URLs, or internal identifiers unless the caller explicitly requests a safe redacted form.

## Boundaries

- Read and summarize only; do not reopen a browser workflow or mutate source records.
- Do not send a notification unless the caller explicitly requests a destination and message action.
- Never invent missing counts. Mark them as unavailable or inconsistent.
