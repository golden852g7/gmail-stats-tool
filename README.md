# 📘 README – Gmail MBOX Stats Tool (v9)

## 🧩 工具简介
`gmail_stats_final_v9.py` 用于分析 **Gmail 导出的 `.mbox`** 文件，提取出：
- 公司名（出现在主题中 `DITTA` 之后，保留 `&`、`'`、`-` 等符号，遇到 `DAL` 等终止词停止）  
- 邮件发送日期（以**邮件的 `Date` 头**为准，缺失时回退到 mbox 的 `From ` 信封行）  
- 每封邮件中 **员工的“状态 + 姓名”**（仅统计一次/人/封，避免重复）

> 输出 CSV 改为三列：**A 列 `company`、B 列 `date`、C 列 `operation_name`**，并按日期排序（同一日期会聚在一起）。

---

## ✅ 关键特性（本版要点）
- **公司名**：从 `Subject` 中的 `DITTA` 后提取；允许字符集：`A–Z 0–9 & ' - /` 与空格；遇到 `DAL` 等**立刻停止**。
- **员工名**：从 `dipendente` 后开始提取，支持跨行；允许全大写或 Title Case；**一旦检测到日期样式或斜杠 `/` 立即截断**。
- **状态识别**：  
  `ASSUNZIONE / PROROGA / VARIAZIONE / DIMISSIONE / DIMISSIONE CLIC LAVORO / LICENZIAMENTO`
- **去重**：同一封邮件，同一员工同一状态**只记 1 次**。
- **日期解析**：  
  1) 优先使用头部 `Date:`；  
  2) 若缺失，回退到 mbox 的 `From <envelope>` 行；  
  3) 仍缺失则留空。输出格式为 `dd/mm/yyyy`。
- **排序**：最终按 `date` 升序输出。

---

## 🖥️ 命令用法
```bash
python gmail_stats_final_v9.py <mbox_file> --format csv --output result_v9.csv
# 例如仅统计你的发件：
python gmail_stats_final_v9.py Sent_2025_Q3.mbox --sender paghegest@gmail.com --format csv --output result_v9.csv
```

### 参数说明
| 参数 | 含义 | 示例 |
|---|---|---|
| `<mbox_file>` | 待分析的 mbox 文件路径 | `Sent_2025_Q3.mbox` |
| `--sender` | 只统计该发件人发送的邮件 | `--sender paghegest@gmail.com` |
| `--format` | 输出格式（`csv`/`json`/`text`） | `--format csv` |
| `--output` | 输出文件名 | `--output result_v9.csv` |

---

## 📊 输出格式（CSV）
**列：**  
- `company` — 主题 `DITTA` 后的公司名  
- `date` — 邮件发送日期（`Date` 头或 mbox 信封行），格式 `dd/mm/yyyy`  
- `operation_name` — “状态 + 员工姓名”

**示例：**
```csv
company,date,operation_name
HM TREVISO 20093,06/01/2025,PROROGA ARAUJO NARDOTO REBECA CRISTINA
HM TREVISO 20093,20/03/2025,DIMISSIONE CLIC LAVORO ARAUJO NARDOTO REBECA CRISTINA
LU & YAN 20513,01/04/2025,ASSUNZIONE FAROOQ UMAR
U SUSHI 8 S.A.S DI WANG WENTAO 20315,31/05/2025,LICENZIAMENTO LIN YUHAN
BEAUTY NAILS DI LIN YING 20412,30/06/2025,PROROGA ZHU MIMIAO
```

---

## 🔎 提取规则

### 公司名（Company）
- 来源：`Subject`，从 `DITTA` 后开始
- 允许字符：`[A-Z0-9&' /-]`
- 终止词：`DAL`、`->`、`(`、`[`、`dipendente`
- 示例：`... DITTA LU & YAN 20513 DAL 01/04/2025` → `LU & YAN 20513`

### 员工 + 状态（Operation + Employee）
- 来源：`Subject` 与正文
- 员工从 `dipendente` 开始，遇日期样式或 `/` 截断
- 同一封邮件：**每位员工每种状态只统计一次**

### 发送日期（Date）
- 优先：`Date:` 头（系统发送时间）
- 回退：`From ... Mon Mar 24 09:53:02 +0000 2025`
- 统一格式：`dd/mm/yyyy`

---

## 🧪 常见排错
- **结果为空白**：确认 mbox 含发件人及 `DITTA`。  
- **公司名被截断**：遇 `DAL`/括号等属正常终止。  
- **日期空白**：无 `Date` 头且信封行缺失时可能为空。  

---

## 🗂️ 版本更新摘要
- 新增：发送日期以系统时间为准（非正文）  
- 新增：公司名保留 `&`、`'` 等符号  
- 新增：员工名遇日期样式立即截断  
- 优化：CSV 输出改为三列并按日期升序排序

---

## 🪪 版权
作者：殷明（1500692431ym@gmail.com）  
