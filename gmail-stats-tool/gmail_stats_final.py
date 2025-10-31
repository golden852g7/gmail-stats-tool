
import re
import mailbox
import sys
import json
from datetime import datetime

OPERATIONS = [
    "TOTAL_MESSAGES",
    "ASSUNZIONE",
    "PROROGA",
    "VARIAZIONE",
    "DIMISSIONE",
    "DIMISSIONE CLIC LAVORO",
    "LICENZIAMENTO",
]

def extract_employees_from_text(text: str) -> list[str]:
    """提取 dipendente 后的纯大写英文名字（遇小写即停）。"""
    if not text:
        return []
    text = re.sub(r"\s+", " ", text)
    matches = re.findall(r"dipendente\s+([A-Z][A-Z\s']*)(?=\b[^A-Z])", text)
    names = [m.strip() for m in matches if m.strip()]
    return sorted(set(names))


def detect_operations(text: str) -> set[str]:
    """检测正文或标题中出现的状态（严格区分 DIMISSIONE 与 DIMISSIONE CLIC LAVORO）。"""
    found = set()
    if not text:
        return found

    if re.search(r"\bDIMISSIONE\s+CLIC\s+LAVORO\b", text, re.IGNORECASE):
        found.add("DIMISSIONE CLIC LAVORO")
    elif re.search(r"\bDIMISSIONE\b", text, re.IGNORECASE):
        found.add("DIMISSIONE")

    for op in ("ASSUNZIONE", "PROROGA", "VARIAZIONE", "LICENZIAMENTO"):
        if re.search(fr"\b{op}\b", text, re.IGNORECASE):
            found.add(op)
    return found


def extract_company_from_subject(subject: str) -> str | None:
    """从标题中提取公司名（DITTA 后面、不含数字）。"""
    m = re.search(r"DITTA\s+([A-ZÀ-Ü\s'&\.\-]+?)(?=\s*\d|\s*$)", subject, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def parse_email_date(date_str: str) -> datetime | None:
    try:
        return datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
    except Exception:
        return None


def is_in_range(date_obj: datetime, start: str | None, end: str | None) -> bool:
    if not date_obj:
        return False
    if start and date_obj < datetime.strptime(start, "%Y-%m-%d"):
        return False
    if end and date_obj > datetime.strptime(end, "%Y-%m-%d"):
        return False
    return True


def extract_text_from_message(msg) -> str:
    """提取邮件纯文本正文。"""
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                try:
                    parts.append(part.get_payload(decode=True).decode(part.get_content_charset("utf-8"), "ignore"))
                except Exception:
                    continue
        return "\n".join(parts)
    else:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset("utf-8"), "ignore")
        except Exception:
            return msg.get_payload()


def iter_messages(path: str):
    mbox = mailbox.mbox(path)
    for msg in mbox:
        yield msg


def aggregate_all(path: str, start_date=None, end_date=None, case_sensitive=False):
    """核心逻辑：每封邮件对应唯一公司，TOTAL_MESSAGES 仅计一次。"""
    data: dict[str, dict[str, dict[str, int]]] = {}

    for message in iter_messages(path):
        date = parse_email_date(message.get("date", ""))
        if not is_in_range(date, start_date, end_date):
            continue

        subject = message.get("subject", "")
        body = extract_text_from_message(message)
        combined = subject + " " + body if case_sensitive else (subject + " " + body).upper()

        company = extract_company_from_subject(subject) or "UNKNOWN_COMPANY"
        employees = extract_employees_from_text(body) or ["UNKNOWN_EMPLOYEE"]
        ops = detect_operations(combined)

        if company not in data:
            data[company] = {}

        for emp in employees:
            bucket = data[company].setdefault(emp, {op: 0 for op in OPERATIONS})
            for op in ops:
                if op in bucket:
                    bucket[op] += 1

        # 每封邮件仅计一次 TOTAL_MESSAGES（公司层面）
        if employees:
            first_emp = employees[0]
            data[company][first_emp]["TOTAL_MESSAGES"] += 1

    return data


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gmail 邮件统计工具（优化版）")
    parser.add_argument("mbox_path", help=".mbox 文件路径")
    parser.add_argument("--aggregate-all", action="store_true", help="统计所有公司所有员工")
    parser.add_argument("--start-date", help="起始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--format", choices=["text", "json", "csv"], default="text")
    args = parser.parse_args()

    data = aggregate_all(args.mbox_path, args.start_date, args.end_date)

    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        print("company,employee,operation,count")
        for company, emp_data in data.items():
            for emp, counts in emp_data.items():
                first_line = True
                for op, c in counts.items():
                    if c > 0:
                        if first_line:
                            print(f"{company},{emp},{op},{c}")
                            first_line = False
                        else:
                            print(f",,{op},{c}")
    else:
        for company, emp_data in data.items():
            print(f"公司: {company}")
            for emp, counts in emp_data.items():
                print(f"  员工: {emp}")
                for op, c in counts.items():
                    if c > 0:
                        print(f"    {op}: {c}")
                print()

if __name__ == "__main__":
    main()
