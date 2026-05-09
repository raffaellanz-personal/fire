#!/usr/bin/env python3
"""
Fire Claim EMLX Timeline Processor

Run from the root of your local Git repository, for example:

    cd "/Users/raffaelladelprete/Library/Mobile Documents/com~apple~CloudDocs/Documents/Personale/Houses/23 Mays Street/02 Fire/Git"
    python3 scripts/fire_claim_emlx_timeline_processor.py

Default input:
    FireClaimEmail_Claude/

Default output:
    processed/

It creates / refreshes:
    processed/master_timeline.csv
    processed/master_timeline.md
    processed/document_register.csv
    processed/document_register.md
    processed/issue_registers/*.md
    processed/case_theories/*.md
    processed/people_index.csv
    processed/action_items.csv
    processed/README.md

It does NOT move, rename, or alter your raw .emlx files.

Important privacy note:
    This script creates processed summaries that may still contain personal information.
    Keep the repo private unless you deliberately want the material public.
"""

from __future__ import annotations

import argparse
import csv
import email
import html
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from email import policy
from email.message import Message
from email.parser import BytesParser
from email.utils import parsedate_to_datetime, getaddresses
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_INPUT_DIR = Path("FireClaimEmail_Claude")
DEFAULT_OUTPUT_DIR = Path("processed")

ISSUE_KEYWORDS = {
    # Core indemnity / technical scope
    "structural": ["structural", "joist", "load bearing", "load-bearing", "bracing", "beam", "framing", "masonry", "foundation", "cpeng", "engineer", "collapse", "primary structure"],
    "building_consent_code": ["building consent", "schedule 1", "building act", "s112", "section 112", "code", "nzbc", "consent", "council", "natural character", "heritage", "overlay", "lbp", "licensed building practitioner", "code compliance", "ccc"],
    "regulatory_legislative_compliance": ["building act", "privacy act", "fair insurance code", "code", "legislation", "regulation", "regulatory", "statutory", "ombudsman", "ifso", "privacy commissioner", "health and safety", "worksafe", "electricity regulations", "asbestos regulations"],
    "smoke_contamination": ["smoke", "soot", "pah", "voc", "combustion", "contamination", "decontamination", "forensic", "odour", "odor", "seal", "smoke sealing", "chloride", "corrosion", "char", "residue"],
    "electrical": ["electrical", "electrician", "wiring", "switchboard", "cable", "power", "recommission", "make safe", "energise", "electrical safety", "master electrician"],
    "gas_plumbing": ["gas", "plumbing", "plumber", "pipe", "water pipe", "gas line", "gas unit", "hot water", "gasfitter", "gas fitter"],
    "moisture_mould": ["moisture", "mould", "mold", "water", "wet", "dry", "drying", "leak", "humidity", "damp", "water ingress", "moisture mapping"],
    "asbestos": ["asbestos", "acm", "clearance", "hygienist", "contaminated material", "friable", "non-friable"],
    "contents": ["contents", "dispose", "disposal", "inventory", "salvage", "items", "basement contents", "total loss documentation", "replacement value", "single item"],
    "scope_tender_repair": ["scope", "scope of works", "tender", "quote", "repair", "reinstatement", "managed repair", "builder", "methodology", "costing", "variation", "estimate"],
    "temporary_accommodation": ["temporary accommodation", "accommodation", "rent", "out of pocket", "allowance", "alternative accommodation", "uninhabitable"],
    "settlement_strategy": ["settlement", "cash", "sum insured", "write-off", "write off", "total loss", "full and final", "offer", "negotiation", "indemnity", "payout"],

    # Conduct / fairness / transparency
    "legal_complaint": ["lawyer", "wynn", "williams", "shine", "welwyn", "legal", "complaint", "ombudsman", "dispute", "ifso", "without prejudice", "solicitor", "counsel"],
    "insurer_conduct_delay": ["delay", "follow up", "following up", "update", "transparency", "refused", "declined", "waiting", "respond", "response", "good faith", "fair", "fairly", "one sided", "one-sided", "bias", "biased", "independent", "preferred builder", "preferred contractor"],
    "inadequate_investigation": ["inadequate", "not inspected", "before inspection", "without inspection", "not assessed", "premature", "rushed", "sequencing", "hidden damage", "investigate", "investigation", "assessment", "assessor", "expert"],
    "transparency_disclosure_failure": ["transparency", "not disclose", "refuse to provide", "refused to provide", "declined to provide", "share the report", "release the report", "copy of", "documents", "data", "files", "records", "withheld", "redacted", "access request"],

    # Privacy / data governance
    "privacy_access": ["privacy act", "privacy request", "personal information", "access request", "principle 6", "ipp6", "my data", "my information", "provide my files", "copy of my file", "claim file", "data request", "information request"],
    "privacy_breach": ["privacy breach", "breach of privacy", "someone else's", "someone else", "third party", "third-party", "other customer", "other person's", "wrong person", "misdirected", "accidental disclosure", "data breach"],
    "portal_failure": ["portal", "login", "password", "username", "access code", "link", "does not work", "not working", "failed login", "unable to access", "download link", "sharepoint", "dropbox"],
    "data_governance": ["data governance", "record keeping", "document management", "file management", "missing documents", "incomplete", "not complete", "failed to provide", "privacy commissioner", "commissioner"],
}

CASE_THEORIES = {
    "01_indemnity_proper_settlement": {
        "title": "Case 1 — Indemnity / Proper Settlement Amount",
        "description": "What amount is required to properly indemnify Raffaella for house, contents, hidden damage, code upgrades, temporary accommodation, and full reinstatement costs?",
        "issues": ["structural", "building_consent_code", "smoke_contamination", "electrical", "gas_plumbing", "moisture_mould", "asbestos", "contents", "scope_tender_repair", "temporary_accommodation", "settlement_strategy"],
    },
    "02_fairness_good_faith_claims_conduct": {
        "title": "Case 2 — Fairness / Good Faith / Claims Conduct",
        "description": "Did Tower handle the claim fairly, transparently, competently, and without one-sided or premature decision-making?",
        "issues": ["legal_complaint", "insurer_conduct_delay", "inadequate_investigation", "transparency_disclosure_failure", "scope_tender_repair", "temporary_accommodation"],
    },
    "03_privacy_act_data_governance": {
        "title": "Case 3 — Privacy Act / Data Access / Data Governance",
        "description": "Did Tower comply with personal information access obligations, protect third-party information, and maintain proper disclosure and document-management systems?",
        "issues": ["privacy_access", "privacy_breach", "portal_failure", "data_governance", "transparency_disclosure_failure"],
    },
    "04_regulatory_code_legislative_compliance": {
        "title": "Case 4 — Regulatory / Code / Legislative Compliance",
        "description": "Were the proposed works, investigations, scope decisions, and claim handling consistent with applicable codes, statutes, standards, safety requirements, and regulatory expectations?",
        "issues": ["building_consent_code", "regulatory_legislative_compliance", "electrical", "asbestos", "gas_plumbing", "moisture_mould", "structural", "smoke_contamination"],
    },
}

IMPORTANT_SENDERS = [
    "tower.co.nz", "wynnwilliams.co.nz", "assetrestore.co.nz", "prendos", "asurnz", "k2", "fenz", "aucklandcouncil", "privacy.org.nz"
]

@dataclass
class EmailRecord:
    file_path: str
    file_name: str
    file_date_hint: str
    message_date: str
    sort_date: str
    sender: str
    sender_email: str
    to: str
    cc: str
    subject: str
    body_preview: str
    summary: str
    key_issues: list[str] = field(default_factory=list)
    case_theories: list[str] = field(default_factory=list)
    strategic_notes: str = ""
    action_requested: str = ""
    attachments: list[str] = field(default_factory=list)
    confidence: str = "Medium"
    tier: str = "Tier 2 - Operational"

@dataclass
class DocumentRecord:
    document_title: str
    source_email_file: str
    source_email_date: str
    source_email_subject: str
    source_email_sender: str
    document_type: str
    key_issues: list[str]
    case_theories: list[str]
    summary: str
    notes: str
    confidence: str = "Medium"


def strip_emlx_byte_count(raw: bytes) -> bytes:
    first_newline = raw.find(b"\n")
    if first_newline == -1:
        return raw
    first_line = raw[:first_newline].strip()
    return raw[first_newline + 1:] if first_line.isdigit() else raw


def parse_email_file(path: Path) -> Optional[Message]:
    try:
        raw = strip_emlx_byte_count(path.read_bytes())
        return BytesParser(policy=policy.default).parsebytes(raw)
    except Exception as exc:
        print(f"WARN: could not parse {path}: {exc}", file=sys.stderr)
        return None


def header_value(msg: Message, name: str) -> str:
    value = msg.get(name, "")
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()


def parse_date(msg: Message, file_name: str) -> tuple[str, str, str]:
    date_header = header_value(msg, "Date")
    file_hint = ""
    m = re.match(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})", file_name)
    if m:
        file_hint = f"{m.group(1)} {m.group(2).replace('-', ':')}"
    sort_date = "9999-12-31T23:59:59"
    display_date = date_header or file_hint
    try:
        if date_header:
            dt = parsedate_to_datetime(date_header)
            sort_date = dt.isoformat()
            display_date = dt.isoformat()
        elif file_hint:
            dt = datetime.strptime(file_hint, "%Y-%m-%d %H:%M:%S")
            sort_date = dt.isoformat()
            display_date = dt.isoformat()
    except Exception:
        if file_hint:
            sort_date = file_hint.replace(" ", "T")
            display_date = file_hint
    return display_date, sort_date, file_hint


def extract_email_address(header: str) -> str:
    addresses = getaddresses([header])
    return (addresses[0][1] or addresses[0][0]) if addresses else ""


def clean_text(value: str) -> str:
    value = html.unescape(value or "")
    value = value.replace("\xa0", " ")
    value = re.sub(r"=\r?\n", "", value)
    value = value.replace("=E2=80=99", "'").replace("=E2=80=93", "-").replace("=E2=80=98", "'")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def markdown_escape(value: str) -> str:
    """Escape raw email HTML so Markdown preview cannot render/break the page."""
    value = value or ""
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def looks_like_html(value: str) -> bool:
    sample = (value or "")[:5000].lower()
    markers = ["<html", "<body", "<table", "<tr", "<td", "<div", "<span", "</p>", "<br"]
    return sum(marker in sample for marker in markers) >= 2


def html_to_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</p>", "\n", value)
    value = re.sub(r"<[^>]+>", " ", value)
    return clean_text(value)


def extract_text_from_part(part: Message) -> str:
    try:
        content = part.get_content()
        return content if isinstance(content, str) else ""
    except Exception:
        try:
            payload = part.get_payload(decode=True)
            return payload.decode(part.get_content_charset() or "utf-8", errors="replace") if payload else ""
        except Exception:
            return ""


def extract_body_text(msg: Message) -> str:
    text_parts, html_parts = [], []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                continue
            ctype = part.get_content_type()
            if ctype == "text/plain":
                text_parts.append(extract_text_from_part(part))
            elif ctype == "text/html":
                html_parts.append(extract_text_from_part(part))
    else:
        ctype = msg.get_content_type()
        if ctype == "text/html":
            html_parts.append(extract_text_from_part(msg))
        else:
            text_parts.append(extract_text_from_part(msg))
    if text_parts:
        joined_text = "
".join(text_parts)
        if looks_like_html(joined_text):
            return html_to_text(joined_text)
        return clean_text(joined_text)
    if html_parts:
        return html_to_text("\n".join(html_parts))
    return ""


def extract_attachments(msg: Message) -> list[str]:
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            filename = part.get_filename()
            disposition = part.get_content_disposition()
            if filename:
                attachments.append(clean_text(filename))
            elif disposition == "attachment":
                attachments.append("[unnamed attachment]")
    return sorted(set(a for a in attachments if a))


def infer_attachments_from_body(body: str) -> list[str]:
    candidates = set()
    patterns = [
        r"[A-Za-z0-9_ .,&()\-]+\.(?:pdf|docx?|xlsx?|csv|txt|jpg|jpeg|png|heic|mov|mp4)",
        r"ANZ1789[^\n\r.;]*",
        r"39775[^\n\r.;]*Post Fire Structural Assessment[^\n\r.;]*",
        r"Combustion pre-decontamination survey[^\n\r.;]*",
        r"Post fire structural assessment report[^\n\r.;]*",
        r"Prendos Report[^\n\r.;]*",
        r"K2 Environmental[^\n\r.;]*",
        r"ASURNZ Material Damage Report[^\n\r.;]*",
        r"Response to building consent concerns[^\n\r.;]*",
    ]
    for pat in patterns:
        for match in re.finditer(pat, body, flags=re.IGNORECASE):
            title = clean_text(match.group(0)).strip(" -–—:;,.[]()")
            if 4 <= len(title) <= 180:
                candidates.add(title)
    return sorted(candidates)


def split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+", clean_text(text))
    return [p.strip() for p in pieces if len(p.strip()) > 20]


def detect_issues(text: str) -> list[str]:
    lower = text.lower()
    issues = []
    for issue, keywords in ISSUE_KEYWORDS.items():
        if any(k.lower() in lower for k in keywords):
            issues.append(issue)
    return issues


def detect_case_theories(issues: list[str]) -> list[str]:
    issue_set = set(issues)
    cases = []
    for case_key, cfg in CASE_THEORIES.items():
        if issue_set.intersection(cfg["issues"]):
            cases.append(case_key)
    return cases


def detect_action_requested(text: str) -> str:
    sentences = split_sentences(text)
    markers = ["please", "can you", "could you", "request", "require", "advise", "confirm", "provide", "send", "respond", "let us know", "we ask", "we require"]
    hits = []
    for sentence in sentences:
        if any(marker in sentence.lower() for marker in markers):
            hits.append(sentence)
        if len(hits) >= 3:
            break
    return " | ".join(hits)[:900]


def make_summary(subject: str, body: str, attachments: list[str], issues: list[str], cases: list[str]) -> str:
    sentences = split_sentences(body)
    selected = []
    priority_terms = [
        "does not accept", "building consent", "schedule 1", "prendos", "tower", "scope", "structural", "contamination",
        "temporary accommodation", "mould", "moisture", "asbestos", "wiring", "gas", "tender", "privacy", "portal", "password",
        "someone else", "third party", "privacy commissioner", "fair insurance code", "not disclose", "refuse", "report", "claim"
    ]
    for sentence in sentences:
        if any(term in sentence.lower() for term in priority_terms):
            selected.append(sentence)
        if len(selected) >= 4:
            break
    if not selected:
        selected = sentences[:2]
    summary = " ".join(selected).strip() or (f"Email subject: {subject}" if subject else "No body text extracted.")
    if attachments:
        summary += f" Attachments/documents mentioned: {', '.join(attachments[:8])}."
    if issues:
        summary += f" Issues tagged: {', '.join(issues)}."
    if cases:
        summary += f" Case theories: {', '.join(cases)}."
    return summary[:1600]


def determine_tier(sender_email: str, subject: str, body: str, issues: list[str], attachments: list[str]) -> str:
    critical = {
        "structural", "building_consent_code", "regulatory_legislative_compliance", "smoke_contamination", "electrical", "asbestos",
        "scope_tender_repair", "temporary_accommodation", "settlement_strategy", "legal_complaint", "privacy_access", "privacy_breach", "portal_failure", "data_governance",
        "inadequate_investigation", "transparency_disclosure_failure"
    }
    if critical.intersection(issues):
        return "Tier 1 - Critical"
    if attachments:
        return "Tier 1 - Critical"
    if any(domain in sender_email.lower() for domain in IMPORTANT_SENDERS):
        return "Tier 2 - Operational"
    if any(word in f"{subject} {body}".lower() for word in ["meeting", "access", "appointment", "available", "thanks", "thank you"]):
        return "Tier 3 - Administrative"
    return "Tier 2 - Operational"


def strategic_notes_for(issues: list[str], cases: list[str], body: str) -> str:
    notes = []
    lower = body.lower()
    if "does not accept" in lower:
        notes.append("Preserves non-acceptance of Tower's scope while allowing costing or process steps to continue.")
    if "building consent" in lower or "schedule 1" in lower or "section 112" in lower:
        notes.append("Relevant to consent/code-compliance dispute and potential cost escalation.")
    if "prendos" in lower:
        notes.append("Links insurer position to independent expert review by Prendos.")
    if "temporary accommodation" in lower or "out of pocket" in lower:
        notes.append("Relevant to additional accommodation claim and delay-caused loss.")
    if "contamination" in lower or "pah" in lower or "voc" in lower or "soot" in lower or "chloride" in lower:
        notes.append("Relevant to hidden contamination, health/safety scope, and consequential reinstatement dispute.")
    if "privacy_access" in issues:
        notes.append("Relevant to Privacy Act access-to-personal-information track.")
    if "privacy_breach" in issues:
        notes.append("Potential third-party disclosure / data breach evidence; do not publish third-party personal data.")
    if "portal_failure" in issues:
        notes.append("Potential evidence of ineffective access mechanism or failed disclosure process.")
    if "transparency_disclosure_failure" in issues:
        notes.append("Supports transparency/fairness concern and may overlap with claim handling and privacy access issues.")
    if "structural" in issues:
        notes.append("Relevant to repair methodology, structural adequacy, and repair-versus-rebuild position.")
    return " ".join(notes)[:1000]


def document_type_for(title: str) -> str:
    lower = title.lower()
    if lower.endswith(".pdf") or "report" in lower or "assessment" in lower or "survey" in lower:
        return "Report / PDF"
    if "scope" in lower or "quote" in lower or "tender" in lower:
        return "Scope / Tender / Quote"
    if lower.endswith((".jpg", ".jpeg", ".png", ".heic", ".mov", ".mp4")):
        return "Photo / Video"
    if lower.endswith((".doc", ".docx")):
        return "Word document"
    if lower.endswith((".xls", ".xlsx", ".csv")):
        return "Spreadsheet / CSV"
    return "Document"


def process_emlx_files(input_dir: Path) -> tuple[list[EmailRecord], list[DocumentRecord], Counter]:
    records, documents, people = [], [], Counter()
    files = sorted(input_dir.rglob("*.emlx"))
    if not files:
        raise FileNotFoundError(f"No .emlx files found under {input_dir}")

    for path in files:
        msg = parse_email_file(path)
        if msg is None:
            continue
        subject = header_value(msg, "Subject")
        sender = header_value(msg, "From")
        sender_email = extract_email_address(sender)
        to = header_value(msg, "To")
        cc = header_value(msg, "Cc")
        message_date, sort_date, file_date_hint = parse_date(msg, path.name)
        body = extract_body_text(msg)
        attachments = sorted(set(extract_attachments(msg) + infer_attachments_from_body(body)))
        joined = " ".join([subject, sender, to, cc, body, " ".join(attachments)])
        issues = detect_issues(joined)
        cases = detect_case_theories(issues)
        summary = make_summary(subject, body, attachments, issues, cases)
        action_requested = detect_action_requested(body)
        tier = determine_tier(sender_email, subject, body, issues, attachments)
        strategic_notes = strategic_notes_for(issues, cases, body)

        for _name, addr in getaddresses([sender, to, cc]):
            if addr:
                people[addr.lower()] += 1

        record = EmailRecord(
            file_path=str(path), file_name=path.name, file_date_hint=file_date_hint,
            message_date=message_date, sort_date=sort_date, sender=sender, sender_email=sender_email,
            to=to, cc=cc, subject=subject, body_preview=body[:2000], summary=summary,
            key_issues=issues, case_theories=cases, strategic_notes=strategic_notes,
            action_requested=action_requested, attachments=attachments,
            confidence="High" if subject or body else "Low", tier=tier,
        )
        records.append(record)

        for title in attachments:
            doc_issues = detect_issues(" ".join([title, subject, body]))
            doc_cases = detect_case_theories(doc_issues)
            documents.append(DocumentRecord(
                document_title=title, source_email_file=path.name, source_email_date=message_date,
                source_email_subject=subject, source_email_sender=sender,
                document_type=document_type_for(title), key_issues=doc_issues, case_theories=doc_cases,
                summary=f"Document or attachment referenced in email: {subject}"[:600],
                notes="Verify whether this file exists separately if it was only mentioned in the email body.",
                confidence="High",
            ))

    records.sort(key=lambda r: (r.sort_date, r.file_name))
    documents.sort(key=lambda d: (d.source_email_date, d.document_title.lower()))
    return records, documents, people


def reset_output_dir(output_dir: Path, clean: bool) -> None:
    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "issue_registers").mkdir(parents=True, exist_ok=True)
    (output_dir / "case_theories").mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, rows: Iterable[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_timeline(records: list[EmailRecord], output_dir: Path) -> None:
    fields = ["date", "tier", "case_theories", "key_issues", "from", "from_email", "to", "cc", "subject", "summary", "strategic_notes", "action_requested", "attachments", "confidence", "source_file", "body_preview"]
    rows = [{
        "date": r.message_date, "tier": r.tier, "case_theories": "; ".join(r.case_theories), "key_issues": "; ".join(r.key_issues),
        "from": r.sender, "from_email": r.sender_email, "to": r.to, "cc": r.cc, "subject": r.subject, "summary": r.summary,
        "strategic_notes": r.strategic_notes, "action_requested": r.action_requested, "attachments": "; ".join(r.attachments),
        "confidence": r.confidence, "source_file": r.file_path, "body_preview": r.body_preview,
    } for r in records]
    write_csv(output_dir / "master_timeline.csv", rows, fields)

    md = ["# Master Timeline", "", "Generated from local `.emlx` files. Raw files are not moved or edited.", ""]
    for r in records:
        md += [
            f"## {markdown_escape(r.message_date)} — {markdown_escape(r.subject or '[No subject]')}",
            f"- **Tier:** {r.tier}",
            f"- **Case theories:** {', '.join(r.case_theories) if r.case_theories else 'None tagged'}",
            f"- **Key issues:** {', '.join(r.key_issues) if r.key_issues else 'None tagged'}",
            f"- **From:** {markdown_escape(r.sender)}",
            f"- **To:** {markdown_escape(r.to)}",
        ]
        if r.cc:
            md.append(f"- **Cc:** {markdown_escape(r.cc)}")
        md.append(f"- **Summary:** {markdown_escape(r.summary)}")
        if r.strategic_notes:
            md.append(f"- **Strategic notes:** {markdown_escape(r.strategic_notes)}")
        if r.action_requested:
            md.append(f"- **Action requested:** {markdown_escape(r.action_requested)}")
        if r.attachments:
            md.append(f"- **Attachments / documents:** {markdown_escape(', '.join(r.attachments))}")
        md += [f"- **Source file:** `{r.file_path}`", ""]
    (output_dir / "master_timeline.md").write_text("\n".join(md), encoding="utf-8")


def write_document_register(documents: list[DocumentRecord], output_dir: Path) -> None:
    fields = ["document_title", "date", "source_email", "source_sender", "source_subject", "document_type", "summary", "case_theories", "key_issues", "notes", "confidence"]
    seen, rows = set(), []
    for d in documents:
        key = (d.document_title.lower(), d.source_email_file)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "document_title": d.document_title, "date": d.source_email_date, "source_email": d.source_email_file,
            "source_sender": d.source_email_sender, "source_subject": d.source_email_subject, "document_type": d.document_type,
            "summary": d.summary, "case_theories": "; ".join(d.case_theories), "key_issues": "; ".join(d.key_issues),
            "notes": d.notes, "confidence": d.confidence,
        })
    write_csv(output_dir / "document_register.csv", rows, fields)

    md = ["# Document / Attachment Register", "", "Includes MIME attachments plus document titles mentioned inside email bodies.", ""]
    for row in rows:
        md += [
            f"## {markdown_escape(row['document_title'])}", f"- **Date:** {row['date']}", f"- **Source email:** `{row['source_email']}`",
            f"- **Source sender:** {markdown_escape(row['source_sender'])}", f"- **Type:** {row['document_type']}", f"- **Summary:** {markdown_escape(row['summary'])}",
            f"- **Case theories:** {row['case_theories'] or 'None tagged'}", f"- **Key issues:** {row['key_issues'] or 'None tagged'}",
            f"- **Notes:** {markdown_escape(row['notes'])}", ""
        ]
    (output_dir / "document_register.md").write_text("\n".join(md), encoding="utf-8")


def write_issue_registers(records: list[EmailRecord], output_dir: Path) -> None:
    grouped = defaultdict(list)
    for r in records:
        for issue in r.key_issues:
            grouped[issue].append(r)
    issue_dir = output_dir / "issue_registers"
    for issue in ISSUE_KEYWORDS.keys():
        entries = grouped.get(issue, [])
        md = [f"# Issue Register: {issue}", "", f"Total tagged emails: {len(entries)}", ""]
        for r in entries:
            md += [f"## {markdown_escape(r.message_date)} — {markdown_escape(r.subject or '[No subject]')}", f"- **Case theories:** {', '.join(r.case_theories) if r.case_theories else 'None tagged'}", f"- **From:** {markdown_escape(r.sender)}", f"- **Summary:** {markdown_escape(r.summary)}"]
            if r.strategic_notes:
                md.append(f"- **Strategic notes:** {markdown_escape(r.strategic_notes)}")
            if r.attachments:
                md.append(f"- **Documents:** {markdown_escape(', '.join(r.attachments))}")
            md += [f"- **Source:** `{r.file_path}`", ""]
        (issue_dir / f"{issue}.md").write_text("\n".join(md), encoding="utf-8")


def write_case_theory_files(records: list[EmailRecord], output_dir: Path) -> None:
    grouped = defaultdict(list)
    for r in records:
        for case_key in r.case_theories:
            grouped[case_key].append(r)
    case_dir = output_dir / "case_theories"
    for case_key, cfg in CASE_THEORIES.items():
        entries = grouped.get(case_key, [])
        issue_counts = Counter(issue for r in entries for issue in r.key_issues)
        md = [f"# {cfg['title']}", "", cfg["description"], "", f"Total tagged emails: {len(entries)}", "", "## Issue counts", ""]
        for issue, count in issue_counts.most_common():
            md.append(f"- **{issue}:** {count}")
        md += ["", "## Chronological evidence", ""]
        for r in entries:
            md += [
                f"### {r.message_date} — {r.subject or '[No subject]'}",
                f"- **From:** {markdown_escape(r.sender)}",
                f"- **Issues:** {', '.join(r.key_issues) if r.key_issues else 'None tagged'}",
                f"- **Summary:** {markdown_escape(r.summary)}",
            ]
            if r.strategic_notes:
                md.append(f"- **Strategic notes:** {markdown_escape(r.strategic_notes)}")
            if r.attachments:
                md.append(f"- **Documents:** {markdown_escape(', '.join(r.attachments))}")
            md += [f"- **Source:** `{r.file_path}`", ""]
        (case_dir / f"{case_key}.md").write_text("\n".join(md), encoding="utf-8")


def write_people_index(people: Counter, output_dir: Path) -> None:
    write_csv(output_dir / "people_index.csv", [{"email": e, "count": c} for e, c in people.most_common()], ["email", "count"])


def write_action_items(records: list[EmailRecord], output_dir: Path) -> None:
    rows = []
    for r in records:
        if r.action_requested:
            rows.append({"date": r.message_date, "from": r.sender, "subject": r.subject, "action_requested": r.action_requested, "case_theories": "; ".join(r.case_theories), "key_issues": "; ".join(r.key_issues), "source_file": r.file_path, "status": "Needs review"})
    write_csv(output_dir / "action_items.csv", rows, ["date", "from", "subject", "action_requested", "case_theories", "key_issues", "source_file", "status"])


def write_readme(output_dir: Path, input_dir: Path, count: int, clean: bool) -> None:
    readme = f"""# Processed Fire Claim Evidence Outputs

Generated from `{input_dir}`.

Files processed: **{count}** `.emlx` emails.

Clean rebuild of processed folder: **{clean}**.

## Key outputs

- `master_timeline.csv` — spreadsheet-friendly chronological timeline.
- `master_timeline.md` — readable timeline with summaries, issues, case theories, and attachments.
- `document_register.csv` — table of attachments and document titles mentioned.
- `document_register.md` — readable document register.
- `issue_registers/` — issue-specific cross-reference files.
- `case_theories/` — four case-theory files:
  - indemnity / proper settlement amount
  - fairness / good faith / claims conduct
  - Privacy Act / data governance
  - regulatory / code / legislative compliance
- `people_index.csv` — email addresses appearing in correspondence.
- `action_items.csv` — extracted requests/actions needing review.

## Important cautions

This is a rule-based extraction. It creates a strong first draft, not a final legal chronology.

Review all Tier 1 entries manually before giving them to lawyers, experts, Tower, IFSO, the Privacy Commissioner, or any court/tribunal.

Do not publish third-party personal information. Keep the repo private unless you intentionally want public access.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build fire claim timeline, document register, issue registers, and case theories from .emlx files.")
    parser.add_argument("input_dir", nargs="?", default=str(DEFAULT_INPUT_DIR), help="Folder containing .emlx files. Default: FireClaimEmail_Claude")
    parser.add_argument("output_dir", nargs="?", default=str(DEFAULT_OUTPUT_DIR), help="Output folder. Default: processed")
    parser.add_argument("--no-clean", action="store_true", help="Do not delete existing processed output folder before rebuilding.")
    return parser.parse_args(argv[1:])


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    clean = not args.no_clean
    if not input_dir.exists():
        print(f"ERROR: input directory does not exist: {input_dir}", file=sys.stderr)
        return 2
    reset_output_dir(output_dir, clean=clean)
    records, documents, people = process_emlx_files(input_dir)
    write_timeline(records, output_dir)
    write_document_register(documents, output_dir)
    write_issue_registers(records, output_dir)
    write_case_theory_files(records, output_dir)
    write_people_index(people, output_dir)
    write_action_items(records, output_dir)
    write_readme(output_dir, input_dir, len(records), clean)
    print(f"Processed {len(records)} emails")
    print(f"Found {len(documents)} document/attachment references")
    print(f"Outputs written to: {output_dir}")
    print("Case theory files written to: processed/case_theories/")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
