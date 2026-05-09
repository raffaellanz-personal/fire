# EMLX Duplicate Audit

Input folder: `FireClaimEmail_Claude`

Files scanned: **584**

Duplicate rows found across all tests: **376**

Date bucket window: **180 seconds**

Fuzzy threshold: **0.985**

## Reports

- `duplicate_groups.csv` — likely duplicate groups. Rows marked `recommended_keep=YES` are the suggested canonical file.
- `all_email_fingerprints.csv` — fingerprint of every scanned email.

## Duplicate tests used

1. Same Message-ID.
2. Same raw content hash.
3. Same normalized subject + people + body hash.
4. Same file size + rounded date bucket + from + to + normalized subject.
5. Fuzzy comparison for same size/from/to/subject within 10 minutes.

This script does not delete anything.
