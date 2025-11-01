#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# gmail_stats_final_v9.py (patched from v8)
# 修复项：
# 1. 公司名保留 & ' 等符号（改进正则 [A-Z0-9&' ]）
# 2. 员工名遇日期截断（正则检测 / 或日期样式即停止）
# 3. 保持与 v8 逻辑完全兼容

import argparse
import csv
import json
import mailbox
import re
from email.header import decode_header, make_header
from email import policy
from email import message_from_binary_file
from email.message import Message

# token considered valid part of UPPER token (letters/digits and a few symbols)
UPPER_TOKEN_RE = re.compile(r"^[A-Z0-9][A-Z0-9.&'\-/]*$")
TITLE_TOKEN_RE = re.compile(r"^[A-ZÀ-ÖØ-Ý][a-zà-öø-ý'’\-.]*$")
STOP_NAME_TOKENS = re.compile(r"(?i)^(DAL|DALLE|DA|DAL:|->|›|»|\(|\[)$")
DATE_TOKEN_RE = re.compile(r"\d+/\d+/\d+")

STATUS_ORDER = [
    "DIMISSIONE CLIC LAVORO",
    "DIMISSIONE",
    "PROROGA",
    "VARIAZIONE",
    "ASSUNZIONE",
    "LICENZIAMENTO",
]

STATUS_PATTERNS = [
    (re.compile(r"\bDIMISSIONE(?:\s+CON)?\s+CLIC\s*LAVORO\b", re.IGNORECASE), "DIMISSIONE CLIC LAVORO"),
    (re.compile(r"\bDIMISSIONE\w*\b|\bDIMESS[OA]\b", re.IGNORECASE), "DIMISSIONE"),
    (re.compile(r"\bPROROG\w*\b", re.IGNORECASE), "PROROGA"),
    (re.compile(r"\bVARIAZION\w*\b", re.IGNORECASE), "VARIAZIONE"),
    (re.compile(r"\bASSUNZION\w*\b|\bASSUNT[OA]\b", re.IGNORECASE), "ASSUNZIONE"),
    (re.compile(r"\bLICENZIAMENT\w*\b|\bLICENZIAT[OA]\b", re.IGNORECASE), "LICENZIAMENTO"),
]

def normalize_ws(s: str) -> str:
    if not s:
        return ""
    s = s.replace("=\r\n", "").replace("=\n", "")
    s = s.replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def decode_mime_words(s):
    if s is None:
        return ""
    try:
        return str(make_header(decode_header(s)))
    except Exception:
        return s

def extract_text_from_message(msg: Message) -> str:
    texts = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype in ("text/plain", "text/html"):
                try:
                    payload = part.get_payload(decode=True)
                    if payload is None:
                        continue
                    charset = part.get_content_charset() or "utf-8"
                    text = payload.decode(charset, errors="replace")
                except Exception:
                    text = part.get_content() if hasattr(part, 'get_content') else ''
                if ctype == "text/html":
                    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
                    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
                    text = re.sub(r"(?is)<[^>]+>", " ", text)
                texts.append(text)
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload is not None:
                charset = msg.get_content_charset() or "utf-8"
                texts.append(payload.decode(charset, errors="replace"))
            else:
                texts.append(msg.get_payload())
        except Exception:
            texts.append(msg.get_payload())
    return normalize_ws(" ".join(filter(None, texts)))

DITTA_PATTERN = re.compile(r"(?i)D\s*I\s*T\s*T\s*A\b")

def last_ditta_index(subject: str):
    if not subject:
        return None
    pos = None
    for m in DITTA_PATTERN.finditer(subject):
        pos = m.end()
    return pos

def extract_company_from_subject(subject: str) -> str:
    if not subject:
        return ""
    subj = normalize_ws(subject)
    idx = last_ditta_index(subj)
    if idx is None:
        return ""
    tail = subj[idx:]
    cut_points = []
    for pat in [r"->", r"—", r"–", r"\(", r"\[", r"\bdipendente\b", r"\bDAL\b"]:
        m = re.search(pat, tail, re.IGNORECASE)
        if m:
            cut_points.append(m.start())
    if cut_points:
        tail = tail[:min(cut_points)]

    tokens = []
    for raw_tok in tail.strip().split():
        tok = raw_tok.strip(" ,;:")
        if not tok:
            continue
        if UPPER_TOKEN_RE.match(tok) and tok.upper() == tok:
            tokens.append(tok)
        elif tok.isdigit():
            tokens.append(tok)
        else:
            break
    if not tokens:
        return ""
    name = " ".join(tokens).strip()
    letters_only = re.sub(r"[^A-Z]", "", name)
    if len(letters_only) < 2:
        return ""
    return name

def is_upper_token(tok: str) -> bool:
    return bool(UPPER_TOKEN_RE.match(tok)) and tok.upper() == tok

def collect_name_tokens(tokens, start_idx):
    i = start_idx
    caps = []
    while i < len(tokens):
        t = tokens[i].strip(",.;:>")
        if not t or DATE_TOKEN_RE.match(t):
            break
        if is_upper_token(t):
            caps.append(t)
            i += 1
            continue
        break
    if caps:
        return " ".join(caps), i
    return "", start_idx

def extract_employees_from_text(text: str):
    res = set()
    for m in re.finditer(r"\bdipendente\b", text, re.IGNORECASE):
        segment = text[m.end(): m.end() + 600]
        segment = normalize_ws(segment)
        toks = segment.split()
        if not toks:
            continue
        name, _ = collect_name_tokens(toks, 0)
        if len(re.sub(r"[^A-Z]", "", name)) >= 2:
            res.add(name)
    return res

def find_status_for_employee(window: str, subject: str) -> str:
    for rx, label in STATUS_PATTERNS:
        if rx.search(window):
            return label
    for rx, label in STATUS_PATTERNS:
        if rx.search(subject or ''):
            return label
    return ''

def main():
    ap = argparse.ArgumentParser(description='Count per-company emails and per-employee statuses from Gmail mbox.')
    ap.add_argument('mbox_path', help='Path to .mbox file')
    ap.add_argument('--sender', help='Only include messages sent by this address (From matches contains)')
    ap.add_argument('--format', choices=['csv', 'json', 'text'], default='csv')
    ap.add_argument('--output', default='result_v9.csv')
    args = ap.parse_args()

    mbox = mailbox.mbox(args.mbox_path, factory=lambda f: message_from_binary_file(f, policy=policy.default))
    company_totals = {}
    per_emp_status = {}

    for msg in mbox:
        if args.sender:
            fromv = decode_mime_words(msg.get('From', ''))
            if args.sender.lower() not in (fromv or '').lower():
                continue

        subj = decode_mime_words(msg.get('Subject', ''))
        if last_ditta_index(subj) is None:
            continue

        company = extract_company_from_subject(subj)
        if not company:
            continue

        body = extract_text_from_message(msg)
        text = subj + ' \n ' + body
        employees = extract_employees_from_text(text)
        if not employees:
            continue

        company_totals[company] = company_totals.get(company, 0) + 1
        for emp in employees:
            status = find_status_for_employee(text, subj)
            if not status:
                continue
            key = (company, emp, status)
            per_emp_status[key] = per_emp_status.get(key, 0) + 1

    rows = []
    for company, cnt in sorted(company_totals.items()):
        rows.append({'company': company, 'employee': '', 'operation': 'TOTAL_MESSAGES', 'count': cnt})
    for (company, emp, status), cnt in sorted(per_emp_status.items()):
        rows.append({'company': company, 'employee': emp, 'operation': status, 'count': cnt})

    if args.format == 'csv':
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=['company', 'employee', 'operation', 'count'])
            w.writeheader()
            w.writerows(rows)
        print(f'Wrote CSV: {args.output}')
    elif args.format == 'json':
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f'Wrote JSON: {args.output}')
    else:
        for r in rows:
            print('{company}\t{employee}\t{operation}\t{count}'.format(**r))

if __name__ == '__main__':
    main()
