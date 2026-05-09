# EMLX Duplicate Audit — Updated

Input folder: `FireClaimEmail_Claude`

Files scanned: **265**

Duplicate rows found across all tests: **32**

Date bucket window: **180 seconds**

Fuzzy threshold: **0.985**

## Reports

- `duplicate_groups.csv` — likely duplicate groups. Rows marked `recommended_keep=YES` are suggested canonical files.
- `all_email_fingerprints.csv` — fingerprint of every scanned email.

## Duplicate tests used

1. Same Message-ID.
2. Same raw content hash.
3. Same normalized subject + people + body hash.
4. Same file size + rounded date bucket + from + to + normalized subject.
5. Same sender + same day + same normalized body. This catches Apple Mail draft/outbox/sent repeats.
6. Fuzzy comparison for same size + sender + subject.

This script does not delete anything.
