
from __future__ import annotations

import argparse
import datetime as dt
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime
import json
import mailbox
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, Optional, List, Set

OPERATIONS = (
    "ASSUNZIONE",
    "PROROGA",
    "VARIAZIONE",
    "DIMISSIONE",
    "DIMISSIONE CLIC LAVORO",
    "LICENZIAMENTO",
)

_RE_DITTA = re.compile(r"\bDITTA\s+([A-Z][A-Z\s&'\.\-]+?)(?=\s*\d|\s*$)", re.IGNORECASE)
_RE_DIPENDENTI = re.compile(r"\bdipendente\s+([A-Z][A-Z\s'\-]+)", re.IGNORECASE)

_PATTERNS = [
    ("DIMISSIONE CLIC LAVORO", re.compile(r"\bDIMISSIONE\s+CLIC\s+LAVORO\b", re.IGNORECASE)),
    ("DIMISSIONE", re.compile(r"\bDIMISSIONE\b(?!\s+CLIC\s+LAVORO)", re.IGNORECASE)),
    ("ASSUNZIONE", re.compile(r"\bASSUNZIONE\b", re.IGNORECASE)),
    ("PROROGA", re.compile(r"\bPROROGA\b", re.IGNORECASE)),
    ("VARIAZIONE", re.compile(r"\bVARIAZIONE\b", re.IGNORECASE)),
    ("LICENZIAMENTO", re.compile(r"\bLICENZIAMENTO\b", re.IGNORECASE)),
]

def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyse a Gmail Takeout mbox file and summarise how many "
            "messages mention a specific employee and employment operation, "
            "or aggregate counts for all companies/employees."
        )
    )
    parser.add_argument("mbox", type=Path, nargs="?", help="Path to the Gmail .mbox export (required unless generating sample data)")
    parser.add_argument("--employee", help="Full name of the employee to search for inside the messages (single-employee mode).")
    parser.add_argument("--start-date", type=_parse_date_arg, help="Inclusive start date (YYYY-MM-DD).")
    parser.add_argument("--end-date", type=_parse_date_arg, help="Inclusive end date (YYYY-MM-DD).")
    parser.add_argument("--case-sensitive", action="store_true", help="Match the employee and operations using case sensitive search (single-employee mode).")
    parser.add_argument("--format", choices=("text", "json", "csv"), default="text", help="Format of the output summary.")
    parser.add_argument("--create-sample-mbox", type=Path, metavar="PATH", help="Write a demo .mbox file with example messages and exit.")
    parser.add_argument("--aggregate-all", action="store_true", help="Aggregate counts for ALL companies and employees.")
    return parser.parse_args(argv)

def _parse_date_arg(value: str) -> dt.date:
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:  # pragma: no cover - argparse displays the error
        raise argparse.ArgumentTypeError(str(exc)) from exc

def parse_email_date(raw_date: str) -> Optional[dt.datetime]:
    if not raw_date:
        return None
    try:
        parsed = parsedate_to_datetime(raw_date)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)

def _coerce_range(start_date: Optional[dt.date], end_date: Optional[dt.date]) -> tuple[Optional[dt.datetime], Optional[dt.datetime]]:
    start_dt = (
        dt.datetime.combine(start_date, dt.time.min, tzinfo=dt.timezone.utc)
        if start_date
        else None
    )
    end_dt = (
        dt.datetime.combine(end_date, dt.time.max, tzinfo=dt.timezone.utc)
        if end_date
        else None
    )
    return start_dt, end_dt

def iter_messages(path: Path) -> Iterable[Message]:
    if not path.exists():
        raise FileNotFoundError(f"Mbox file not found: {path}")
    box = mailbox.mbox(path)
    try:
        for message in box:
            yield message
    finally:
        box.close()

def write_sample_mbox(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    box = mailbox.mbox(path)
    try:
        box.lock()
        box.clear()

        def _add(subject: str, date: str, body: str) -> None:
            message = mailbox.mboxMessage()
            message.set_from("reporter@example.com")
            message["To"] = "manager@example.com"
            message["Subject"] = subject
            message["Date"] = date
            message.set_payload(body)
            box.add(message)

        _add(
            "1 VARIAZIONE ORARIO DITTA HM TREVISO 20093",
            "Mon, 01 Jan 2024 10:00:00 +0000",
            "Buongiorno,\n\ndipendente BAYATI MD HRIDOY variazione ...\n",
        )
        _add(
            "2 PROROGHE DITTA HM TREVISO 20093",
            "Tue, 02 Jan 2024 12:00:00 +0000",
            "dipendente BITTOLO MATTEO proroga fino al 31/12/2025.\n"
            "dipendente GALLEGOS SALGUERO JEAN CARLOS proroga fino al 31/08/2025.\n",
        )
        _add(
            "Comunicazione dimissione - DITTA ACME",
            "Wed, 10 Jan 2024 12:00:00 +0000",
            "Il dipendente MARIO ROSSI ha inoltrato DIMISSIONE CLIC LAVORO.",
        )
        box.flush()
    finally:
        box.close()
    return path

def extract_plain_text(message: Message) -> str:
    if message.is_multipart():
        parts: list[str] = []
        for part in message.walk():
            if part.get_content_maintype() != "text":
                continue
            if part.get_content_subtype() != "plain":
                continue
            payload = part.get_payload(decode=True)
            charset = part.get_content_charset() or "utf-8"
            if payload is None:
                text = part.get_payload()
                if isinstance(text, str):
                    parts.append(text)
                    continue
                if text is None:
                    payload = b""
                else:
                    payload = str(text).encode("utf-8", errors="replace")
            try:
                parts.append(payload.decode(charset, errors="replace"))
            except LookupError:
                parts.append(payload.decode("utf-8", errors="replace"))
        return "\n".join(parts)

    payload_bytes = message.get_payload(decode=True)
    if payload_bytes is not None:
        charset = message.get_content_charset() or "utf-8"
        try:
            return payload_bytes.decode(charset, errors="replace")
        except LookupError:
            return payload_bytes.decode("utf-8", errors="replace")

    payload = message.get_payload()
    if isinstance(payload, str):
        return payload
    if payload is None:
        return ""
    return str(payload)

def extract_company_from_subject(subject: str) -> Optional[str]:
    if not subject:
        return None
    m = _RE_DITTA.search(subject)
    if not m:
        return None
    company = m.group(1).strip()
    return company if company and not any(ch.isdigit() for ch in company) else None

def extract_employees_from_text(text: str) -> List[str]:
    if not text:
        return []
    names = []
    for m in _RE_DIPENDENTI.findall(text):
        name = m.strip()
        if name and name.upper() == name:
            names.append(name)
    seen = set()
    uniq = []
    for n in names:
        if n not in seen:
            uniq.append(n)
            seen.add(n)
    return uniq

def detect_operations(text: str) -> Set[str]:
    found: Set[str] = set()
    if not text:
        return found
    for op, pat in _PATTERNS:
        if pat.search(text):
            found.add(op)
    return found

def message_matches_employee(message: Message, employee: str, *, case_sensitive: bool) -> bool:
    addresses = getaddresses([message.get("To", ""), message.get("Cc", ""), message.get("Bcc", "")])
    formatted_addresses = " ".join(
        filter(None, (f"{name} {addr}" if name else addr for name, addr in addresses))
    )
    haystacks = [
        message.get("Subject", ""),
        formatted_addresses,
        extract_plain_text(message),
    ]
    if case_sensitive:
        return any(employee in haystack for haystack in haystacks)
    lowered_employee = employee.lower()
    return any(lowered_employee in haystack.lower() for haystack in haystacks)

def analyse_mbox(path: Path, employee: str, *, start_date: Optional[dt.date] = None, end_date: Optional[dt.date] = None, case_sensitive: bool = False) -> Dict[str, int]:
    start_dt, end_dt = _coerce_range(start_date, end_date)
    totals = {op: 0 for op in OPERATIONS}
    total_messages = 0
    for message in iter_messages(path):
        message_date = parse_email_date(message.get("Date"))
        if message_date is None:
            continue
        if start_dt and message_date < start_dt:
            continue
        if end_dt and message_date > end_dt:
            continue
        if not message_matches_employee(message, employee, case_sensitive=case_sensitive):
            continue

        total_messages += 1
        body = extract_plain_text(message)
        subject = message.get("Subject", "")

        combined_text = f"{subject}\n{body}"
        haystack = combined_text if case_sensitive else combined_text.upper()

        for operation in OPERATIONS:
            needle = operation if case_sensitive else operation.upper()
            if needle in haystack:
                totals[operation] += 1

    totals["TOTAL_MESSAGES"] = total_messages
    return totals

def aggregate_all(path: Path, start_date: Optional[dt.date], end_date: Optional[dt.date]) -> Dict[str, Dict[str, Dict[str, int]]]:
    start_dt, end_dt = _coerce_range(start_date, end_date)
    data: Dict[str, Dict[str, Dict[str, int]]] = {}
    for message in iter_messages(path):
        msg_dt = parse_email_date(message.get("Date"))
        if msg_dt is None:
            continue
        if start_dt and msg_dt < start_dt:
            continue
        if end_dt and msg_dt > end_dt:
            continue

        subject = message.get("Subject", "") or ""
        body = extract_plain_text(message) or ""
        combined = f"{subject}\n{body}"

        company = extract_company_from_subject(subject) or "UNKNOWN_COMPANY"
        employees = extract_employees_from_text(body) or ["UNKNOWN_EMPLOYEE"]
        ops = detect_operations(combined)

        for emp in employees:
            bucket = data.setdefault(company, {}).setdefault(emp, {op: 0 for op in OPERATIONS})
            bucket.setdefault("TOTAL_MESSAGES", 0)
            bucket["TOTAL_MESSAGES"] += 1
            for op in ops:
                if op in bucket:
                    bucket[op] += 1
    return data

def _format_text_output(stats: Dict[str, int], employee: str, start: str, end: str) -> str:
    lines = [
        f"Statistiche per '{employee}'",
        f"Intervallo date: {start or '-'} → {end or '-'}",
        "",
        f"Totale messaggi: {stats['TOTAL_MESSAGES']}",
    ]
    for operation in OPERATIONS:
        lines.append(f"  {operation}: {stats[operation]}")
    return "\n".join(lines)

def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)

    if args.create_sample_mbox:
        write_sample_mbox(args.create_sample_mbox)
        print(
            "已生成示例邮箱导出:"
            f" {args.create_sample_mbox}\n"
            "示例包含多员工与多状态的测试邮件，可用于练习命令。"
        )
        if not args.mbox:
            return 0

    if not args.mbox:
        print("error: the mbox path is required unless generating sample data", file=sys.stderr)
        return 2
    if not args.aggregate_all and not args.employee:
        print("error: --employee is required unless using --aggregate-all", file=sys.stderr)
        return 2

    if args.aggregate_all:
        agg = aggregate_all(args.mbox, args.start_date, args.end_date)
        if args.format == "json":
            print(json.dumps({
                "start_date": args.start_date.isoformat() if args.start_date else None,
                "end_date": args.end_date.isoformat() if args.end_date else None,
                "statistics": agg
            }, indent=2, ensure_ascii=False))
        elif args.format == "csv":
            import csv
            writer = csv.writer(sys.stdout, lineterminator="\n")
            writer.writerow(["company", "employee", "operation", "count"])
            for company, emps in agg.items():
                for emp, stats in emps.items():
                    writer.writerow([company, emp, "TOTAL_MESSAGES", stats.get("TOTAL_MESSAGES", 0)])
                    for op in OPERATIONS:
                        writer.writerow([company, emp, op, stats.get(op, 0)])
        else:
            period = f"{args.start_date.isoformat() if args.start_date else '-'} → {args.end_date.isoformat() if args.end_date else '-'}"
            print(f"Aggregate statistics (date range: {period})\n")
            for company, emps in agg.items():
                print(f"== COMPANY: {company}")
                for emp, stats in emps.items():
                    print(f"  -- EMPLOYEE: {emp}")
                    print(f"     TOTAL_MESSAGES: {stats.get('TOTAL_MESSAGES', 0)}")
                    for op in OPERATIONS:
                        print(f"     {op}: {stats.get(op, 0)}")
            print("\n(Use --format csv to export as CSV)")
        return 0

    stats = analyse_mbox(
        args.mbox,
        args.employee,
        start_date=args.start_date,
        end_date=args.end_date,
        case_sensitive=args.case_sensitive,
    )

    if args.format == "json":
        payload = {
            "employee": args.employee,
            "start_date": args.start_date.isoformat() if args.start_date else None,
            "end_date": args.end_date.isoformat() if args.end_date else None,
            "statistics": stats,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            _format_text_output(
                stats,
                args.employee,
                args.start_date.isoformat() if args.start_date else "",
                args.end_date.isoformat() if args.end_date else "",
            )
        )
    return 0

if __name__ == "__main__":  # pragma: no cover - manual execution only
    sys.exit(main())
