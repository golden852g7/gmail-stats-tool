
# 📊 Gmail 邮件状态统计工具（多公司 + 多员工版）

本工具可用于分析 Gmail 导出的 `.mbox` 邮件文件，自动识别并统计：  
- 各公司（公司名出现在主题中 “DITTA” 后面）  
- 各员工（正文中 “dipendente” 后面的大写名字）  
- 六种雇佣状态关键词出现次数  

---

## 🧩 功能特性

✅ 支持统计 Gmail **发件箱**中所有邮件  
✅ 自动提取：  
- 公司名（从标题中 “DITTA” 后面抽取，不含数字）  
- 员工姓名（从正文中 “dipendente” 后提取，支持多员工）  
✅ 严格区分 6 种状态（不会混算）  
- ASSUNZIONE（签）  
- PROROGA（续签）  
- VARIAZIONE（改）  
- DIMISSIONE（关）  
- DIMISSIONE CLIC LAVORO（工会离职）  
- LICENZIAMENTO（解雇）  
✅ 支持日期范围筛选（--start-date / --end-date）  
✅ 支持输出格式：text（默认）/ json / csv  
✅ 支持单员工统计与全量汇总模式  

---

## ⚙️ 使用方法

确保系统中已安装 **Python 3.9+**。  
然后在命令行进入仓库目录：

```bash
cd gmail-stats-tool
```

### 1️⃣ 生成示例数据

```bash
python gmail_stats.py --create-sample-mbox demo.mbox
```

生成的 `demo.mbox` 中包含多员工、多状态测试邮件，可用于练习命令。

---

### 2️⃣ 汇总所有公司 + 员工（推荐）

#### 📋 文本输出（默认）
```bash
python gmail_stats.py mail.mbox --aggregate-all --start-date 2025-07-01 --end-date 2025-08-31
```

#### 📈 导出 CSV（适合 Excel 分析）
```bash
python gmail_stats.py mail.mbox --aggregate-all --start-date 2025-07-01 --end-date 2025-08-31 --format csv > stats.csv
```

#### 🧾 导出 JSON
```bash
python gmail_stats.py mail.mbox --aggregate-all --format json > stats.json
```

---

### 3️⃣ 单一员工统计（旧模式兼容）

```bash
python gmail_stats.py mail.mbox --employee "BAYATI MD HRIDOY" --start-date 2025-08-01 --end-date 2025-08-31
```

---

## 🧮 输出说明

### 文本输出（默认）
```text
Aggregate statistics (date range: 2025-07-01 → 2025-08-31)

== COMPANY: HM TREVISO
  -- EMPLOYEE: BITTOLO MATTEO
     TOTAL_MESSAGES: 3
     PROROGA: 2
     VARIAZIONE: 1
```

### CSV 输出
| company | employee | operation | count |
|----------|-----------|------------|-------|
| HM TREVISO | BITTOLO MATTEO | TOTAL_MESSAGES | 3 |
| HM TREVISO | BITTOLO MATTEO | PROROGA | 2 |
| HM TREVISO | BITTOLO MATTEO | VARIAZIONE | 1 |

---

## 📁 文件结构

```
gmail-stats-tool/
├── gmail_stats.py      # 主脚本（最新版）
├── mail.mbox           # 你的 Gmail 发件箱导出文件
├── demo.mbox           # 示例文件（可选）
├── README.md           # 使用说明
└── tests/              # 测试目录（可选）
```

---

## 🧠 逻辑摘要

- 公司名提取：从主题中匹配 `DITTA` 后的文本（不含数字）  
- 员工名提取：正文中 `dipendente` 后的全大写名字，可多次出现  
- 状态匹配：使用正则精准匹配 6 种关键词  
- 每封邮件可能涉及多个员工，逐一统计  
- 每个公司-员工组合都有自己的统计记录  

---

## 🧰 示例：测试逻辑（多员工邮件）

**邮件内容示例：**
```
2 PROROGHE DITTA HM TREVISO 20093

dipendente BITTOLO MATTEO proroga fino al 31/12/2025.
dipendente GALLEGOS SALGUERO JEAN CARLOS proroga fino al 31/08/2025.
```

**统计结果：**
| 公司 | 员工 | PROROGA | TOTAL_MESSAGES |
|------|------|----------|----------------|
| HM TREVISO | BITTOLO MATTEO | 1 | 1 |
| HM TREVISO | GALLEGOS SALGUERO JEAN CARLOS | 1 | 1 |

---

## 🧩 参数参考

| 参数 | 说明 |
|------|------|
| `mbox` | Gmail 导出的 `.mbox` 文件路径 |
| `--aggregate-all` | 启用全公司汇总模式 |
| `--employee` | 指定单员工统计 |
| `--start-date` / `--end-date` | 日期范围（YYYY-MM-DD） |
| `--format` | 输出格式：`text` / `json` / `csv` |
| `--create-sample-mbox` | 生成示例文件 |
| `--case-sensitive` | 区分大小写匹配（一般不用） |

---

## 🧾 注意事项

- 默认匹配不区分大小写。  
- 邮件日期按 UTC 比较。  
- 公司名中若出现数字会被自动忽略。  
- 未检测到公司或员工时，使用 `UNKNOWN_COMPANY` / `UNKNOWN_EMPLOYEE` 占位。

---

## ✨ 示例命令快速参考

```bash
# 汇总统计
python gmail_stats.py mail.mbox --aggregate-all --format csv > result.csv

# 按员工统计
python gmail_stats.py mail.mbox --employee "MARIO ROSSI"

# 生成演示文件
python gmail_stats.py --create-sample-mbox demo.mbox
```

---

作者：YM 
最后更新：2025-10-31
