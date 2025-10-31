
# Gmail 邮件统计工具（Final 版本）

## 📌 功能简介
该工具用于分析导出的 Gmail 邮件（`.mbox` 文件），统计每个公司下各员工的操作状态次数。

支持的状态：
- ASSUNZIONE（签）
- PROROGA（续签）
- VARIAZIONE（改）
- DIMISSIONE（辞职）
- DIMISSIONE CLIC LAVORO（工会辞职）
- LICENZIAMENTO（解雇）

---

## ⚙️ 功能特性

### ✅ 1. 自动识别员工姓名
- 自动匹配正文中 `dipendente` 后的**全大写英文字符串**；
- 一旦检测到小写字母、数字或标点符号立即停止；
- 支持多名员工（根据多个 `dipendente` 出现次数识别）；
- 自动去重。

示例：

```
dipendente BITTOLO MATTEO proroga fino al 31/12/2025.
dipendente GALLEGOS SALGUERO JEAN CARLOS proroga fino al 31/08/2025.
```

识别结果：
```
["BITTOLO MATTEO", "GALLEGOS SALGUERO JEAN CARLOS"]
```

---

### ✅ 2. 严格区分辞职类型
- 匹配到 **DIMISSIONE CLIC LAVORO** 时，仅记入该类型；
- 若仅出现 **DIMISSIONE**，则记为普通辞职；
- 两者不会混算。

---

### ✅ 3. 每封邮件只计一次 TOTAL_MESSAGES
- 每封邮件仅属于一个公司；
- 即使包含多个员工，也仅在该公司下累计一封。

---

### ✅ 4. CSV 输出优化
导出命令：
```bash
python gmail_stats_final.py demo.mbox --aggregate-all --format csv > stats.csv
```

示例输出：

| company | employee | operation | count |
|----------|-----------|------------|-------|
| HM TREVISO | BAYATI MD HRIDOY | TOTAL_MESSAGES | 1 |
|            |                     | VARIAZIONE | 1 |
| HM TREVISO | BITTOLO MATTEO | TOTAL_MESSAGES | 1 |
|            |                     | PROROGA | 1 |
| ACME | MARIO ROSSI | TOTAL_MESSAGES | 1 |
|      |             | DIMISSIONE CLIC LAVORO | 1 |

✅ 每个公司与员工仅在首行输出，后续状态行留空，更直观、清晰。

---

### ✅ 5. 命令行参数
| 参数 | 说明 |
|------|------|
| `--aggregate-all` | 汇总所有公司所有员工 |
| `--start-date` | 过滤起始日期（YYYY-MM-DD） |
| `--end-date` | 过滤截止日期（YYYY-MM-DD） |
| `--format` | 输出格式（text / json / csv） |

---

## 🧪 测试与验证
运行以下命令进行自动化测试：
```bash
pytest tests/test_gmail_stats.py -v
```

---

### ⚙️ 环境要求
- Python ≥ 3.9
- 依赖库：`mailbox`, `re`, `json`
