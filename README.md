
# Gmail 邮件统计工具（Final 版本）

## 📤 如何获取 Gmail 邮件的 `.mbox` 文件

1. 打开 **Google Takeout**：  
   👉 https://takeout.google.com/

2. 在导出内容中，**仅勾选「Gmail」** 服务。

3. 点击「下一步」，选择导出格式：  
   - 文件类型：`.zip`  
   - 频率：一次性导出  
   - 文件大小：建议选 2GB 或 4GB  

4. 点击「创建导出」，等待 Google 打包。

5. **确保仅导出已发送邮件（Sent Mail）**：  
   在导出设置中点击「包含的邮件标签」(*All mail data included*)，  
   取消全选后，仅勾选 **Sent Mail（已发送邮件）**。  
   这样导出的 `.mbox` 文件只包含你自己发出的邮件。

   导出完成后，下载压缩包并解压，通常可在以下路径找到：  
   ```
   Takeout/Mail/Sent Mail.mbox
   ```

   📍 即为可用于本工具的 `.mbox` 邮件文件。

6. 将 `.mbox` 文件放入你的项目根目录（例如与 `gmail_stats_final.py` 同一文件夹）。

7. 在命令行中运行统计命令，例如：  
   ```bash
   python gmail_stats_final.py "Sent Mail.mbox" --aggregate-all --format csv > result.csv
   ```

8. 如需指定统计日期范围，可加入以下参数：  
   ```bash
   python gmail_stats_final.py "Sent Mail.mbox"        --aggregate-all        --start-date 2025-01-01        --end-date 2025-10-31        --format csv > result.csv
   ```

   📘 参数说明：  
   - `--start-date`：统计起始日期（含当天）；  
   - `--end-date`：统计截止日期（含当天）；  
   - 日期格式：`YYYY-MM-DD`；  
   - 若不指定，则默认统计 `.mbox` 文件中的所有邮件。

---

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
