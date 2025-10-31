# Gmail 邮件统计工具 v2

该工具可用于统计 Gmail 已发送邮件中，不同公司、不同员工在指定时间内的操作状态数量。

---

## 🧭 一、导出 Gmail 已发送邮件 (Sent Mail)

1. 打开 [Google Takeout](https://takeout.google.com/)
2. 在导出内容中，**仅勾选「Gmail」** 服务。
3. 点击 **“下一步”**，然后配置导出选项：  
   - 文件类型：`.zip`  
   - 频率：**一次性导出**  
   - 文件大小：建议选择 2GB 或 4GB  
4. 点击「创建导出」，等待 Google 打包。  
5. 导出完成后，下载压缩包并解压，找到以下路径之一：  

   ```bash
   Takeout/Mail/Sent.mbox
   Takeout/Mail/已发送邮件.mbox
   ```

   📌 **该文件仅包含你发送出去的邮件**，非常适合本工具分析使用。

6. 将 `.mbox` 文件放到项目根目录（与 `gmail_stats_final_v2.py` 同一文件夹）。

---

## ⚙️ 二、运行环境

确保系统中已安装 **Python 3.9+**。

进入命令行，进入项目根目录：

```bash
cd /path/to/gmail-stats-tool
```

---

## 📊 三、执行统计命令

### 基本命令

```bash
python gmail_stats_final_v2.py Sent.mbox --aggregate-all --format csv > result.csv
```

### 可选参数

| 参数 | 说明 |
|------|------|
| `--start-date YYYY-MM-DD` | 统计开始日期（可选） |
| `--end-date YYYY-MM-DD` | 统计结束日期（可选） |
| `--format [text/json/csv]` | 输出格式（默认 text） |
| `--aggregate-all` | 聚合所有公司统计 |

示例：

```bash
python gmail_stats_final_v2.py Sent.mbox --start-date 2025-01-01 --end-date 2025-03-31 --format csv > result.csv
```

---

## 🧩 四、分析逻辑说明

1. **公司名称**：从邮件标题中提取 `DITTA` 后紧跟的字符串（不包含数字）。  
2. **员工姓名**：从正文中提取 `dipendente` 后连续的大写字母字符串（遇小写即停止）。  
3. **状态关键字**：共 6 种（区分大小写、严格匹配）：  
   - `ASSUNZIONE`（签约）  
   - `PROROGA`（续签）  
   - `VARIAZIONE`（变更）  
   - `DIMISSIONE`（辞职）  
   - `DIMISSIONE CLIC LAVORO`（工会离职）  
   - `LICENZIAMENTO`（解雇）  
4. **统计规则**：  
   - 每封邮件只计一次 `TOTAL_MESSAGES`（按公司维度）  
   - 每位员工单独统计其状态次数  
   - `DIMISSIONE` 与 `DIMISSIONE CLIC LAVORO` 严格区分，不混算  

---

## 🧪 五、测试示例

可使用自带测试文件 `demo_v2.mbox` 进行验证：

```bash
python gmail_stats_final_v2.py demo_v2.mbox --aggregate-all --format csv > test_result.csv
```

输出示例：

| company | employee | operation | count |
|----------|-----------|------------|-------|
| HM TREVISO |  | TOTAL_MESSAGES | 2 |
| HM TREVISO | BAYATI MD HRIDOY | VARIAZIONE | 1 |
| HM TREVISO | BITTOLO MATTEO | PROROGA | 1 |
| HM TREVISO | GALLEGOS SALGUERO JEAN CARLOS | PROROGA | 1 |
| ACME |  | TOTAL_MESSAGES | 1 |
| ACME | MARIO ROSSI | DIMISSIONE CLIC LAVORO | 1 |

---

## 📁 六、结果查看

导出为 CSV 时，可直接使用 Excel 或 Numbers 打开：

```bash
result.csv
```

或导出 JSON：

```bash
python gmail_stats_final_v2.py Sent.mbox --format json > result.json
```

---

## 💬 七、备注

- 仅统计“发件箱”邮件。  
- 若想重新生成示例文件，可使用：  

  ```bash
  python gmail_stats_final_v2.py --create-sample demo.mbox
  ```

---
