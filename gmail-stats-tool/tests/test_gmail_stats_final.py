
import pytest
from gmail_stats_final import extract_employees_from_text, detect_operations

def test_extract_employees_uppercase_only():
    text = "dipendente BITTOLO MATTEO proroga fino al 31/12/2025."
    assert extract_employees_from_text(text) == ["BITTOLO MATTEO"]

def test_extract_multiple_employees():
    text = "dipendente BITTOLO MATTEO proroga fino al 31/12/2025. dipendente GALLEGOS SALGUERO JEAN CARLOS proroga fino al 31/08/2025."
    result = extract_employees_from_text(text)
    assert set(result) == {"BITTOLO MATTEO", "GALLEGOS SALGUERO JEAN CARLOS"}

def test_detect_operations_separation():
    assert detect_operations("ha inoltrato DIMISSIONE CLIC LAVORO") == {"DIMISSIONE CLIC LAVORO"}
    assert detect_operations("ha presentato DIMISSIONE volontaria") == {"DIMISSIONE"}

def test_csv_formatting_output(tmp_path):
    data = {
        "HM TREVISO": {
            "BITTOLO MATTEO": {"TOTAL_MESSAGES": 1, "PROROGA": 1},
            "GALLEGOS SALGUERO JEAN CARLOS": {"TOTAL_MESSAGES": 1, "PROROGA": 1},
        }
    }
    csv_path = tmp_path / "out.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("company,employee,operation,count\n")
        for company, emp_data in data.items():
            for emp, counts in emp_data.items():
                first_line = True
                for op, c in counts.items():
                    if c > 0:
                        if first_line:
                            f.write(f"{company},{emp},{op},{c}\n")
                            first_line = False
                        else:
                            f.write(f",,{op},{c}\n")

    result = csv_path.read_text(encoding="utf-8").strip().splitlines()
    assert result[0].startswith("company,employee")
    assert result[1].startswith("HM TREVISO,BITTOLO MATTEO,")
    assert ",,PROROGA,1" in result[-1]
