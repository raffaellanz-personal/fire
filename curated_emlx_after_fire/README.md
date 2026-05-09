# Curated EMLX Review Set

Input folder: `FireClaimEmail_Claude`

Start date: `2025-05-18`

Raw emails scanned: **584**

Relevant candidate emails after date/relevance filters: **581**

Unique emails copied to review set: **581**

Duplicates excluded: **0**

Skipped as not relevant / before date / unparseable: **3**

## Important

This script does not delete or alter raw evidence. It copies one canonical version of each selected email into `emlx_review_set/`.

Duplicates are detected primarily by Message-ID, then by normalized subject/people/body hash.

Review `curated_index.csv`, `duplicates_report.csv`, and `skipped_report.csv` before relying on the curated folder as complete.
