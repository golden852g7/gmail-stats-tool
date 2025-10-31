
import pytest
from pathlib import Path
from gmail_stats import (
    write_sample_mbox,
    analyse_mbox,
    aggregate_all,
    extract_company_from_subject,
    extract_employees_from_text,
    detect_operations,
)

# ----------------------------
# 原有测试（单员工模式）
# ----------------------------

def test_analyse_mbox_single_employee(tmp_path):
    mbox_path = tmp_path / "demo.mbox"
    write_sample_mbox(mbox_path)

    stats = analyse_mbox(mbox_path, "BAYATI MD HRIDOY")
    assert isinstance(stats, dict)
    assert "TOTAL_MESSAGES" in stats
    assert all(op in stats for op in [
        "ASSUNZIONE", "PROROGA", "VARIAZIONE", "DIMISSIONE",
        "DIMISSIONE CLIC LAVORO", "LICENZIAMENTO"
    ])

def test_write_sample_mbox_creates_file(tmp_path):
    mbox_path = tmp_path / "sample.mbox"
    path = write_sample_mbox(mbox_path)
    assert path.exists()

# ----------------------------
# 新增测试（多员工 + 多公司模式）
# ----------------------------

def test_extract_company_and_employees_parsing():
    subj = "2 PROROGHE DITTA HM TREVISO 20093"
    body = (
        "dipendente BITTOLO MATTEO proroga fino al 31/12/2025.\n"
        "dipendente GALLEGOS SALGUERO JEAN CARLOS proroga fino al 31/08/2025.\n"
    )
    company = extract_company_from_subject(subj)
    employees = extract_employees_from_text(body)
    ops = detect_operations(body)

    assert company == "HM TREVISO"
    assert set(employees) == {"BITTOLO MATTEO", "GALLEGOS SALGUERO JEAN CARLOS"}
    assert "PROROGA" in ops

def test_detect_operations_strict_matching():
    text = "DIMISSIONE CLIC LAVORO confermata. DIMISSIONE altra non vale."
    ops = detect_operations(text)
    assert "DIMISSIONE CLIC LAVORO" in ops
    assert "DIMISSIONE" in ops  # 允许同时出现，但不会混算

def test_aggregate_all_counts_multiple_employees(tmp_path):
    mbox_path = tmp_path / "multi.mbox"
    write_sample_mbox(mbox_path)
    data = aggregate_all(mbox_path, None, None)

    # 确认结构
    assert isinstance(data, dict)
    assert "HM TREVISO" in data
    hm_data = data["HM TREVISO"]

    # 至少识别到 2 名员工
    assert len(hm_data) >= 2
    found = any(emp for emp in hm_data if "MATTEO" in emp or "JEAN" in emp)
    assert found, "应识别出多个员工"

    # 状态验证
    any_proroga = any(stats["PROROGA"] > 0 for stats in hm_data.values())
    assert any_proroga, "至少有一名员工应统计到 PROROGA"
