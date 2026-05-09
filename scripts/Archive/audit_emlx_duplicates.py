#!/usr/bin/env python3
"""
Fire Claim EMLX Duplicate Audit

Purpose:
    Find likely duplicate .emlx emails using several signals:
      - file size
      - actual email Date header, rounded to a time window
      - From / To / Cc
      - normalized subject
      - normalized body/content hash
      - raw content hash
      - optional fuzzy similarity for near-duplicates

It does NOT delete, move, or alter any original email files.

Recommended run from Git repo root:

    cd "/Users/raffaelladelprete/Library/Mobile Documents/com~apple~CloudDocs/Documents/Personale/Houses/23 Mays Street/02 Fire/Git"
    python3 scripts/audit_emlx_duplicates.py FireClaimEmail_Claude duplicate_audit

Or audit the curated set:

    python3 scripts/audit_emlx_duplicates.py curated_emlx_after_fire/emlx_review_set duplicate_audit_curated

Outputs:
    duplicate_audit/duplicate_groups.csv
    duplicate_audit/all_email_fingerprints.csv
    duplicate_audit/README.md
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Optional

DEFAULT_DATE_WINDOW_SECONDS = 180  # 3 minutes. Your examples differ by ~30–150 seconds.
DEFAULT_FUZZY_THRESHOLD = 0.985

@dataclass
class EmailFP:
    path: Path
    filename: str
    size: int
    date: Optional[datetime]
    date_iso: str
    date_bucket: str
    from_email: str
    to_emails: str
    cc_emails: str
    people_key: str
    subject: str
    subject_key: str
    message_id: str
    raw_hash: str
    body_hash: str
    body_preview: str
    duplicate_key_strict: str
    duplicate_key_loose: str


def strip_emlx_byte_count(raw: bytes) -> bytes:
    first_newline = raw.find(b"\n")
    if first_newline == -1:
        return raw
    first_line = raw[:first_newline].strip()
    return raw[first_newline + 1:] if first_line.isdigit() else raw


def parse_msg(path: Path) -> Optional[Message]:
    try:
        raw = strip_emlx_byte_count(path.read_bytes())
        return BytesParser(policy=policy.default).parsebytes(raw)
    except Exception as exc:
        print(f"WARN: could not parse {path}: {exc}", file=sys.stderr)
        return None


def header(msg: Optional[Message], name: str) -> str:
    if msg is None:
        return ""
    return str(msg.get(name, "") or "").replace("\r", " ").replace("\n", " ").strip()


def parse_date(msg: Optional[Message], filename: str, window_seconds: int) -> tuple[Optional[datetime], str, str]:
    date_header = header(msg, "Date")
    dt = None
    try:
        if date_header:
            dt = parsedate_to_datetime(date_header)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
    except Exception:
        dt = None

    if dt is None:
        m = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})", filename)
        if m:
            try:
                dt = datetime.strptime(f"{m.group(1)} {m.group(2).replace('-', ':')}", "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc)
            except Exception:
                dt = None

    if dt is None:
        return None, "", "unknown"

    epoch = int(dt.timestamp())
    bucket_epoch = (epoch // window_seconds) * window_seconds
    bucket = datetime.fromtimestamp(bucket_epoch, tz=timezone.utc).isoformat()
    return dt, dt.isoformat(), bucket


def clean_text(value: str) -> str:
    value = value or ""
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</p>", "\n", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def part_text(part: Message) -> str:
    try:
        content = part.get_content()
        return content if isinstance(content, str) else ""
    except Exception:
        try:
            payload = part.get_payload(decode=True)
            if payload:
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            return ""
    return ""


def body_text(msg: Optional[Message]) -> str:
    if msg is None:
        return ""
    texts, htmls = [], []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type() == "text/plain":
                texts.append(part_text(part))
            elif part.get_content_type() == "text/html":
                htmls.append(part_text(part))
    else:
        if msg.get_content_type() == "text/html":
            htmls.append(part_text(msg))
        else:
            texts.append(part_text(msg))
    return clean_text("\n".join(texts or htmls))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def normalize_subject(subject: str) -> str:
    subject = subject or ""
    while True:
        new = re.sub(r"^\s*(re|fw|fwd):\s*", "", subject, flags=re.I)
        if new == subject:
            break
        subject = new
    subject = re.sub(r"\s+", " ", subject).strip().lower()
    return subject


def normalize_body(body: str) -> str:
    body = body or ""
    # Remove common quoted reply chains and signatures enough to detect duplicate exported copies.
    body = re.sub(r"(?is)\bOn .{0,200}? wrote:\s*.*$", "", body)
    body = re.sub(r"(?is)From:\s+.*?Subject:\s+.*$", "", body)
    body = re.sub(r"(?is)Sent from my iPhone.*$", "", body)
    body = re.sub(r"\s+", " ", body).strip().lower()
    return body


def emails_from_headers(headers: list[str]) -> list[str]:
    return sorted(set(addr.lower() for _name, addr in getaddresses(headers) if addr))


def fingerprint(path: Path, window_seconds: int) -> EmailFP:
    raw = path.read_bytes()
    raw_wo_count = strip_emlx_byte_count(raw)
    msg = parse_msg(path)
    dt, date_iso, date_bucket = parse_date(msg, path.name, window_seconds)
    from_h = header(msg, "From")
    to_h = header(msg, "To")
    cc_h = header(msg, "Cc")
    from_email = (emails_from_headers([from_h]) or [""])[0]
    to_emails = ";".join(emails_from_headers([to_h]))
    cc_emails = ";".join(emails_from_headers([cc_h]))
    people_key = ";".join(emails_from_headers([from_h, to_h, cc_h]))
    subject = header(msg, "Subject")
    subject_key = normalize_subject(subject)
    message_id = (header(msg, "Message-ID") or header(msg, "Message-Id")).lower().strip()
    body = body_text(msg)
    normalized_body = normalize_body(body)
    raw_hash = sha256_bytes(raw_wo_count)
    body_hash = sha256_text(normalized_body[:20000])

    # Strict: same body, subject, people.
    duplicate_key_strict = "|".join([subject_key, people_key, body_hash])

    # Loose: same size + subject + from/to + date bucket. Useful for your observed duplicates.
    duplicate_key_loose = "|".join([str(path.stat().st_size), date_bucket, subject_key, from_email, to_emails])

    return EmailFP(
        path=path,
        filename=path.name,
        size=path.stat().st_size,
        date=dt,
        date_iso=date_iso,
        date_bucket=date_bucket,
        from_email=from_email,
        to_emails=to_emails,
        cc_emails=cc_emails,
        people_key=people_key,
        subject=subject,
        subject_key=subject_key,
        message_id=message_id,
        raw_hash=raw_hash,
        body_hash=body_hash,
        body_preview=normalized_body[:500],
        duplicate_key_strict=duplicate_key_strict,
        duplicate_key_loose=duplicate_key_loose,
    )


def group_by(items: list[EmailFP], attr: str) -> dict[str, list[EmailFP]]:
    groups: dict[str, list[EmailFP]] = {}
    for item in items:
        key = getattr(item, attr)
        if key:
            groups.setdefault(key, []).append(item)
    return {k: v for k, v in groups.items() if len(v) > 1}


def fuzzy_groups(items: list[EmailFP], threshold: float) -> list[list[EmailFP]]:
    """Find near-duplicates among emails already sharing size/from/to/subject/date_bucket-ish.
    Kept deliberately conservative to avoid slow all-vs-all comparison.
    """
    pre_groups: dict[str, list[EmailFP]] = {}
    for item in items:
        key = "|".join([str(item.size), item.subject_key, item.from_email, item.to_emails])
        pre_groups.setdefault(key, []).append(item)

    result = []
    for group in pre_groups.values():
        if len(group) < 2:
            continue
        used = set()
        for i, a in enumerate(group):
            if i in used:
                continue
            cluster = [a]
            used.add(i)
            for j, b in enumerate(group[i + 1:], start=i + 1):
                if j in used:
                    continue
                # Only compare if dates are within 10 minutes or missing.
                if a.date and b.date and abs((a.date - b.date).total_seconds()) > 600:
                    continue
                sim = SequenceMatcher(None, a.body_preview, b.body_preview).ratio()
                if sim >= threshold:
                    cluster.append(b)
                    used.add(j)
            if len(cluster) > 1:
                result.append(cluster)
    return result


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def add_group_rows(rows: list[dict], group_type: str, groups: list[list[EmailFP]]) -> None:
    for group_no, group in enumerate(groups, start=1):
        canonical = sorted(group, key=lambda x: (x.date or datetime.max.replace(tzinfo=timezone.utc), len(x.filename), x.filename))[0]
        for item in sorted(group, key=lambda x: x.filename):
            rows.append({
                "group_type": group_type,
                "group_no": group_no,
                "recommended_keep": "YES" if item.path == canonical.path else "NO",
                "file": str(item.path),
                "canonical_file": str(canonical.path),
                "date": item.date_iso,
                "date_bucket": item.date_bucket,
                "size": item.size,
                "from": item.from_email,
                "to": item.to_emails,
                "cc": item.cc_emails,
                "subject": item.subject,
                "message_id": item.message_id,
                "raw_hash": item.raw_hash,
                "body_hash": item.body_hash,
            })


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit .emlx duplicates by size, date, from/to, subject, and content.")
    parser.add_argument("input_dir", nargs="?", default="FireClaimEmail_Claude")
    parser.add_argument("output_dir", nargs="?", default="duplicate_audit")
    parser.add_argument("--window-seconds", type=int, default=DEFAULT_DATE_WINDOW_SECONDS)
    parser.add_argument("--fuzzy-threshold", type=float, default=DEFAULT_FUZZY_THRESHOLD)
    args = parser.parse_args(argv[1:])

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        print(f"ERROR: input folder not found: {input_dir}", file=sys.stderr)
        return 2

    files = sorted(input_dir.rglob("*.emlx"))
    fps = [fingerprint(p, args.window_seconds) for p in files]

    all_rows = []
    for fp in fps:
        all_rows.append({
            "file": str(fp.path),
            "date": fp.date_iso,
            "date_bucket": fp.date_bucket,
            "size": fp.size,
            "from": fp.from_email,
            "to": fp.to_emails,
            "cc": fp.cc_emails,
            "subject": fp.subject,
            "message_id": fp.message_id,
            "raw_hash": fp.raw_hash,
            "body_hash": fp.body_hash,
            "strict_key": fp.duplicate_key_strict,
            "loose_key": fp.duplicate_key_loose,
        })

    duplicate_rows = []

    msgid_groups = list(group_by([fp for fp in fps if fp.message_id], "message_id").values())
    raw_groups = list(group_by(fps, "raw_hash").values())
    body_groups = list(group_by(fps, "duplicate_key_strict").values())
    loose_groups = list(group_by(fps, "duplicate_key_loose").values())
    fuzzy = fuzzy_groups(fps, args.fuzzy_threshold)

    add_group_rows(duplicate_rows, "same_message_id", msgid_groups)
    add_group_rows(duplicate_rows, "same_raw_content_hash", raw_groups)
    add_group_rows(duplicate_rows, "same_subject_people_body", body_groups)
    add_group_rows(duplicate_rows, "same_size_datebucket_from_to_subject", loose_groups)
    add_group_rows(duplicate_rows, "fuzzy_same_size_from_to_subject", fuzzy)

    write_csv(output_dir / "all_email_fingerprints.csv", all_rows, [
        "file", "date", "date_bucket", "size", "from", "to", "cc", "subject", "message_id", "raw_hash", "body_hash", "strict_key", "loose_key"
    ])
    write_csv(output_dir / "duplicate_groups.csv", duplicate_rows, [
        "group_type", "group_no", "recommended_keep", "file", "canonical_file", "date", "date_bucket", "size", "from", "to", "cc", "subject", "message_id", "raw_hash", "body_hash"
    ])

    readme = f"""# EMLX Duplicate Audit

Input folder: `{input_dir}`

Files scanned: **{len(fps)}**

Duplicate rows found across all tests: **{len(duplicate_rows)}**

Date bucket window: **{args.window_seconds} seconds**

Fuzzy threshold: **{args.fuzzy_threshold}**

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
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    print(f"Scanned: {len(fps)} .emlx files")
    print(f"Duplicate report rows: {len(duplicate_rows)}")
    print(f"Output: {output_dir / 'duplicate_groups.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
