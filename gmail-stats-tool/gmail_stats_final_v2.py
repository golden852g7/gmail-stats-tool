#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import csv
import argparse
import mailbox
from datetime import datetime

OPERATIONS = [
    "ASSUNZIONE",
    "PROROGA",
    "VARIAZIONE",
    "DIMISSIONE CLIC LAVORO",
    "DIMISSIONE",
    "LICENZIAMENTO",
]

def extract_company(subject: str) -> str:
    m = re.search(r"DITTA\s+([A-Z\s]+?)(?=\s*\d|$)", subject or "", re.IGNORECASE)
    return m.group(1).strip().upper() if m else "UNKNOWN_COMPANY"

def extract_employees_from_text(text: str) -> list[str]:
    if not text:
        return []
    text = re.sub(r"\s+", " ", text)
    matches = re.findall(r"dipendente\s+([A-Z\s']+)", text)
    names = []
    for m in matches:
        name = re.split(r"[^A-Z\s']", m.strip())[0].strip()
        if name and name.isupper():
            names.append(name)
    return sorted(set(names))

def extract_operations(text: str) -> list[str]:
    ops_found = []
    for op in OPERATIONS:
        pattern = r"\b" + re.escape(op) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            if op == "DIMISSIONE":
                if re.search(r"DIMISSIONE CLIC LAVORO", text, re.IGNORECASE):
                    continue
            ops_found.append(op)
    return sorted(set(ops_found))

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None

def process_mbox(mbox_path, start_date=None, end_date=None):
    mbox = mailbox.mbox(mbox_path)
    data = {}
    company_message_count = {}

    for msg in mbox:
        subject = msg["subject"] or ""
        date = msg["date"]
        text = msg.get_payload(decode=True)
        try:
            text = text.decode("utf-8", errors="ignore")
        except Exception:
            text = str(text)

        msg_date = None
        if date:
            try:
                msg_date = datetime.strptime(date[:25], "%a, %d %b %Y %H:%M:%S")
            except Exception:
                pass

        if start_date and msg_date and msg_date < start_date:
            continue
        if end_date and msg_date and msg_date > end_date:
            continue

        company = extract_company(subject)
        employees = extract_employees_from_text(text)
        operations = extract_operations(subject + " " + text)

        # 记录公司邮件数
        company_message_count[company] = company_message_count.get(company, 0) + 1

        if company not in data:
            data[company] = {}
        for emp in employees:
            if emp not in data[company]:
                data[company][emp] = {}
            for op in operations:
                data[company][emp][op] = data[company][emp].get(op, 0) + 1

    return data, company_message_count

def write_csv(data, company_message_count, output_file):
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["company", "employee", "operation", "count"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for company, emp_dict in data.items():
            writer.writerow({"company": company, "employee": "", "operation": "TOTAL_MESSAGES", "count": company_message_count.get(company, 0)})
            for emp, ops in emp_dict.items():
                for op, count in ops.items():
                    writer.writerow({"company": "", "employee": emp, "operation": op, "count": count})

def main():
    parser = argparse.ArgumentParser(description="Gmail Email Statistics Tool (v2)")
    parser.add_argument("mbox_path", help="Path to Gmail mbox file")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--format", choices=["csv"], default="csv", help="Output format")
    parser.add_argument("--output", default="result.csv", help="Output CSV filename")
    args = parser.parse_args()

    start_date = parse_date(args.start_date) if args.start_date else None
    end_date = parse_date(args.end_date) if args.end_date else None

    data, company_message_count = process_mbox(args.mbox_path, start_date, end_date)
    write_csv(data, company_message_count, args.output)

    print(f"✅ 统计完成！结果已导出至: {args.output}")

if __name__ == "__main__":
    main()
