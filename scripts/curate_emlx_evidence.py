#!/usr/bin/env python3
"""
Fire Claim EMLX Evidence Curator

Purpose:
    Create a clean review set of relevant .emlx files from a messy Apple Mail export.

It will:
    - scan a raw .emlx folder
    - keep emails dated on/after 18 May 2025 by default
    - select emails involving important people/domains, not just tower.co.nz
    - detect exact and near-duplicates using Message-ID + normalized content hash
    - copy one canonical copy of each selected email into a new folder
    - write CSV reports explaining what was kept, skipped, or treated as duplicate

It does NOT delete, rename, or modify the raw emails.

Recommended run from Git repo root:

    cd "/Users/raffaelladelprete/Library/Mobile Documents/com~apple~CloudDocs/Documents/Personale/Houses/23 Mays Street/02 Fire/Git"
    python3 scripts/curate_emlx_evidence.py

Default input:
    FireClaimEmail_Claude/

Default output:
    curated_emlx_after_fire/

Outputs:
    curated_emlx_after_fire/emlx_review_set/*.emlx
    curated_emlx_after_fire/curated_index.csv
    curated_emlx_after_fire/duplicates_report.csv
    curated_emlx_after_fire/skipped_report.csv
    curated_emlx_after_fire/README.md
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path
from typing import Optional

DEFAULT_INPUT_DIR = Path("FireClaimEmail_Claude")
DEFAULT_OUTPUT_DIR = Path("curated_emlx_after_fire")
DEFAULT_START_DATE = "2025-05-18"

# Add or remove terms here. These are intentionally broader than just Tower.
RELEVANT_DOMAINS = [
    "tower.co.nz",
    "assetrestore.co.nz",
    "wynnwilliams.co.nz",
    "shine",                 # prior legal enquiry, still relevant chronology
    "prendos",
    "asurnz",
    "k2",
    "aucklandcouncil",
    "aucklandcouncil.govt.nz",
    "fenz",
    "fireandemergency.nz",
    "privacy.org.nz",
    "ombudsman",
    "ifso",
    "eqc",
]

RELEVANT_EMAILS = [
    "claims@tower.co.nz",
    "raffaellanz@icloud.com",
]

RELEVANT_SUBJECT_TERMS = [
    "c90306048",
    "23 mays",
    "mays street",
    "devonport",
    "fire",
    "tower claim",
    "tender review",
    "scope",
    "reinstatement",
    "privacy",
    "personal information",
    "claim file",
    "building consent",
    "prendos",
    "asset restore",
    "temporary accommodation",
]

RELEVANT_BODY_TERMS = [
    "c90306048",
    "23 mays",
    "mays street",
    "devonport",
    "tower",
    "asset restore",
    "fire claim",
    "building consent",
    "schedule 1",
    "section 112",
    "privacy act",
    "privacy commissioner",
    "prendos",
    "asbestos",
    "smoke",
    "soot",
    "pah",
    "voc",
    "structural",
    "temporary accommodation",
    "contents",
]

EXCLUDE_DOMAINS = [
    "noreply.github.com",
    "github.com",
]

@dataclass
class ParsedEmail:
    path: Path
    msg: Optional[Message]
    date: Optional[datetime]
    date_display: str
    from_header: str
    from_email: str
    to_header: str
    cc_header: str
    subject: str
    message_id: str
    body_text: str
    raw_size: int
    content_hash: str
    normalized_hash: str
    relevance_reasons: list[str]


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
        print(f"WARN: failed to parse {path}: {exc}", file=sys.stderr)
        return None


def header(msg: Message, name: str) -> str:
    return str(msg.get(name, "") or "").replace("\r", " ").replace("\n", " ").strip()


def parse_date(msg: Message, filename: str) -> tuple[Optional[datetime], str]:
    date_header = header(msg, "Date") if msg else ""
    try:
        if date_header:
            dt = parsedate_to_datetime(date_header)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt, dt.isoformat()
    except Exception:
        pass

    m = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})", filename)
    if m:
        try:
            dt = datetime.strptime(f"{m.group(1)} {m.group(2).replace('-', ':')}", "%Y-%m-%d %H:%M:%S")
            dt = dt.replace(tzinfo=timezone.utc)
            return dt, dt.isoformat()
        except Exception:
            pass
    return None, ""


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
    texts = []
    htmls = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            ctype = part.get_content_type()
            if ctype == "text/plain":
                texts.append(part_text(part))
            elif ctype == "text/html":
                htmls.append(part_text(part))
    else:
        if msg.get_content_type() == "text/html":
            htmls.append(part_text(msg))
        else:
            texts.append(part_text(msg))
    return clean_text("\n".join(texts or htmls))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize_for_duplicate(subject: str, sender: str, to: str, cc: str, body: str) -> str:
    subject = re.sub(r"^(re|fw|fwd):\s*", "", subject.strip(), flags=re.I)
    body = re.sub(r"\bOn .* wrote:\s*.*$", "", body, flags=re.I | re.S)
    body = re.sub(r"From: .*?Subject: .*", "", body, flags=re.I | re.S)
    body = re.sub(r"\s+", " ", body).strip().lower()
    people = " ".join(sorted(set(a.lower() for _n, a in getaddresses([sender, to, cc]) if a)))
    return f"subj={subject.lower()}\npeople={people}\nbody={body[:5000]}"


def safe_filename(value: str, max_len: int = 180) -> str:
    value = value.strip().replace("/", "-")
    value = re.sub(r"[^A-Za-z0-9@._+\-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value[:max_len] or "email"


def email_addresses(headers: list[str]) -> list[str]:
    return [addr.lower() for _name, addr in getaddresses(headers) if addr]


def relevance(parsed: ParsedEmail) -> list[str]:
    reasons = []
    all_headers = " ".join([parsed.from_header, parsed.to_header, parsed.cc_header]).lower()
    addresses = email_addresses([parsed.from_header, parsed.to_header, parsed.cc_header])
    subject_l = parsed.subject.lower()
    body_l = parsed.body_text.lower()

    if any(domain in all_headers for domain in EXCLUDE_DOMAINS):
        return []

    for domain in RELEVANT_DOMAINS:
        if domain.lower() in all_headers:
            reasons.append(f"party/domain:{domain}")

    for email_addr in RELEVANT_EMAILS:
        if email_addr.lower() in addresses:
            reasons.append(f"email:{email_addr}")

    for term in RELEVANT_SUBJECT_TERMS:
        if term.lower() in subject_l:
            reasons.append(f"subject:{term}")

    # Body terms are useful but weaker, so only scan first part for speed/noise control.
    body_sample = body_l[:12000]
    for term in RELEVANT_BODY_TERMS:
        if term.lower() in body_sample:
            reasons.append(f"body:{term}")

    # Avoid keeping every personal email just because Raffaella is in the mailbox.
    strong = [r for r in reasons if not r.startswith("email:raffaellanz")]
    return sorted(set(reasons)) if strong else []


def parse_email(path: Path) -> ParsedEmail:
    msg = parse_msg(path)
    dt, date_display = parse_date(msg, path.name) if msg else (None, "")
    from_h = header(msg, "From") if msg else ""
    to_h = header(msg, "To") if msg else ""
    cc_h = header(msg, "Cc") if msg else ""
    subject = header(msg, "Subject") if msg else ""
    message_id = header(msg, "Message-ID") or header(msg, "Message-Id") if msg else ""
    body = body_text(msg)
    raw = path.read_bytes()
    raw_wo_count = strip_emlx_byte_count(raw)
    content_hash = sha256_bytes(raw_wo_count)
    normalized = normalize_for_duplicate(subject, from_h, to_h, cc_h, body)
    parsed = ParsedEmail(
        path=path,
        msg=msg,
        date=dt,
        date_display=date_display,
        from_header=from_h,
        from_email=(email_addresses([from_h]) or [""])[0],
        to_header=to_h,
        cc_header=cc_h,
        subject=subject,
        message_id=message_id.strip().lower(),
        body_text=body,
        raw_size=path.stat().st_size,
        content_hash=content_hash,
        normalized_hash=sha256_text(normalized),
        relevance_reasons=[],
    )
    parsed.relevance_reasons = relevance(parsed)
    return parsed


def canonical_sort_key(p: ParsedEmail) -> tuple:
    # Prefer actual message Date, shorter/cleaner filename, and non-iCloud placeholder weirdness.
    return (
        p.date or datetime.max.replace(tzinfo=timezone.utc),
        len(p.path.name),
        p.path.name.lower(),
    )


def build_output_name(p: ParsedEmail, index: int) -> str:
    dt = p.date or datetime.max.replace(tzinfo=timezone.utc)
    date_part = dt.strftime("%Y_%m_%d_%H_%M_%S") if p.date else "unknown_date"
    sender = safe_filename(p.from_email or "unknown_sender", 60)
    tos = email_addresses([p.to_header])
    primary_to = safe_filename(tos[0] if tos else "unknown_to", 60)
    subj = safe_filename(re.sub(r"^(re|fw|fwd):\s*", "", p.subject, flags=re.I), 60)
    return f"{date_part}__{sender}__to__{primary_to}__{index:04d}__{subj}.emlx"


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Curate relevant post-fire .emlx files and remove duplicates from review set.")
    parser.add_argument("input_dir", nargs="?", default=str(DEFAULT_INPUT_DIR))
    parser.add_argument("output_dir", nargs="?", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--start-date", default=DEFAULT_START_DATE, help="Keep emails on/after this date, YYYY-MM-DD. Default: 2025-05-18")
    parser.add_argument("--no-clean", action="store_true", help="Do not delete existing output folder first")
    args = parser.parse_args(argv[1:])

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    review_dir = output_dir / "emlx_review_set"

    if not input_dir.exists():
        print(f"ERROR: input folder not found: {input_dir}", file=sys.stderr)
        return 2

    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    if output_dir.exists() and not args.no_clean:
        shutil.rmtree(output_dir)
    review_dir.mkdir(parents=True, exist_ok=True)

    parsed_all: list[ParsedEmail] = []
    for path in sorted(input_dir.rglob("*.emlx")):
        parsed_all.append(parse_email(path))

    skipped_rows = []
    candidates = []
    for p in parsed_all:
        if not p.date:
            skipped_rows.append({"file": str(p.path), "reason": "no_parseable_date", "subject": p.subject})
            continue
        if p.date < start_dt:
            skipped_rows.append({"file": str(p.path), "reason": "before_start_date", "date": p.date_display, "subject": p.subject})
            continue
        if not p.relevance_reasons:
            skipped_rows.append({"file": str(p.path), "reason": "not_relevant_by_rules", "date": p.date_display, "subject": p.subject})
            continue
        candidates.append(p)

    # Duplicate groups. Message-ID is best when present. Fall back to normalized content.
    groups: dict[str, list[ParsedEmail]] = {}
    for p in candidates:
        key = f"msgid:{p.message_id}" if p.message_id else f"norm:{p.normalized_hash}"
        groups.setdefault(key, []).append(p)

    kept: list[ParsedEmail] = []
    duplicate_rows = []
    for key, group in groups.items():
        group = sorted(group, key=canonical_sort_key)
        canonical = group[0]
        kept.append(canonical)
        for dup in group[1:]:
            duplicate_rows.append({
                "duplicate_file": str(dup.path),
                "kept_file": str(canonical.path),
                "duplicate_basis": key,
                "date": dup.date_display,
                "from": dup.from_header,
                "to": dup.to_header,
                "subject": dup.subject,
                "size": dup.raw_size,
                "content_hash": dup.content_hash,
                "normalized_hash": dup.normalized_hash,
            })

    kept = sorted(kept, key=canonical_sort_key)
    index_rows = []
    for i, p in enumerate(kept, start=1):
        output_name = build_output_name(p, i)
        output_path = review_dir / output_name
        shutil.copy2(p.path, output_path)
        index_rows.append({
            "review_file": str(output_path),
            "original_file": str(p.path),
            "date": p.date_display,
            "from": p.from_header,
            "to": p.to_header,
            "cc": p.cc_header,
            "subject": p.subject,
            "message_id": p.message_id,
            "size": p.raw_size,
            "content_hash": p.content_hash,
            "normalized_hash": p.normalized_hash,
            "relevance_reasons": "; ".join(p.relevance_reasons),
        })

    write_csv(output_dir / "curated_index.csv", index_rows, [
        "review_file", "original_file", "date", "from", "to", "cc", "subject", "message_id", "size", "content_hash", "normalized_hash", "relevance_reasons"
    ])
    write_csv(output_dir / "duplicates_report.csv", duplicate_rows, [
        "duplicate_file", "kept_file", "duplicate_basis", "date", "from", "to", "subject", "size", "content_hash", "normalized_hash"
    ])
    write_csv(output_dir / "skipped_report.csv", skipped_rows, sorted({k for row in skipped_rows for k in row.keys()}))

    readme = f"""# Curated EMLX Review Set

Input folder: `{input_dir}`

Start date: `{args.start_date}`

Raw emails scanned: **{len(parsed_all)}**

Relevant candidate emails after date/relevance filters: **{len(candidates)}**

Unique emails copied to review set: **{len(kept)}**

Duplicates excluded: **{len(duplicate_rows)}**

Skipped as not relevant / before date / unparseable: **{len(skipped_rows)}**

## Important

This script does not delete or alter raw evidence. It copies one canonical version of each selected email into `emlx_review_set/`.

Duplicates are detected primarily by Message-ID, then by normalized subject/people/body hash.

Review `curated_index.csv`, `duplicates_report.csv`, and `skipped_report.csv` before relying on the curated folder as complete.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")

    print(f"Scanned: {len(parsed_all)} .emlx files")
    print(f"Relevant candidates: {len(candidates)}")
    print(f"Unique copied: {len(kept)}")
    print(f"Duplicates excluded: {len(duplicate_rows)}")
    print(f"Output: {review_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
