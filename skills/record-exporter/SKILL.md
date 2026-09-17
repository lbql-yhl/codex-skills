---
name: record-exporter
description: Export validated structured records into a deterministic, human-reviewable folder or archive without mutating the source dataset. Use when a workflow needs grouped Markdown, JSON, CSV, or text exports.
---

# Record exporter

Turn structured records into a predictable export package. The skill does not assume a particular database, browser, CRM, or desktop location.

## Inputs

Accept:

- records or a read-only query result;
- grouping fields, naming rules, and the desired format;
- an explicit destination directory or archive path;
- optional redaction and sorting rules.

## Workflow

1. Confirm that the source is read-only for this operation.
2. Validate the required fields and report incomplete records.
3. Normalize filenames and remove path separators, control characters, and secrets.
4. Group records deterministically using the requested keys.
5. Sort records and fields consistently so repeated exports are diffable.
6. Write a manifest containing export time, record counts, grouping rules, and warnings.
7. Verify that every expected record is represented and that no source records were deleted or changed.

## Output

Depending on the request, create:

- grouped Markdown summaries for human review;
- JSON or CSV machine-readable exports;
- an export manifest and warnings file;
- optionally a compressed archive.

Keep only the fields needed for the requested review. Redact credentials, access tokens, session data, full secrets, and unnecessary personal information.

## Boundaries

- Never delete, overwrite, or mutate source records.
- Refuse to write outside the explicit destination.
- Avoid following symlinks or exporting hidden credential files.
