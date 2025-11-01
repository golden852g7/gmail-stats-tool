# 📘 README – Gmail MBOX Stats Tool (v9)

## 🧩 项目简介
`gmail_stats_final_v9.py` 是一个用于分析 **Gmail 导出的 .mbox 文件** 的统计工具。  
它可以自动提取：
- 每家公司发送或接收的邮件总数；
- 每封邮件中涉及的员工姓名；
- 员工对应的操作类型（如 ASSUNZIONE、PROROGA、DIMISSIONE 等）。

最终输出一个结构化表格（CSV/JSON），方便统计或导入数据库。

---

## ⚙️ 功能特性（v9 版本更新）

**v9 是基于 v8 的稳定增强版，主要修复与改进如下：**

| 修复项 | 描述 |
|--------|------|
| ✅ 公司名支持特殊符号 | 改进正则 `UPPER_TOKEN_RE`，允许 `&`、`'`、`-` 等符号（如 “LU & YAN” 不再被截断）。 |
| ✅ 员工名日期截断 | 检测类似 `01/01/1995` 的日期样式时自动停止提取，避免将日期错误包含在姓名中。 |
| ✅ 完全兼容旧逻辑 | 保持与 v8 一致的提取流程、输出格式及排序逻辑，保证无兼容性问题。 |
| ✅ 稳定性增强 | 修复部分编码异常、空行、MIME 多层嵌套问题。 |

---

## 🖥️ 使用方法

### 0. 前提

**确保Python版本3.9+，下载最新版本即可：https://www.python.org/downloads/**
**安装时能打勾的都勾上，安装结束按Win键输入"cmd"回车进入"命令提示符"窗口，输入**
```bash
python -V
```
**确认Python是否安装成功及其版本，确认正确后进入你下载的"gmail-stats-tool"文件夹，页面正上方有一小条显示文件夹路径的区域，点击，输入"cmd"，进入该文件夹路径下的"命令提示符"窗口进行后续操作**

### 1. 命令行基本用法
```bash
python gmail_stats_final_v9.py <mbox文件路径> [选项]
```

### 2. 可用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `<mbox_path>` | 要分析的 `.mbox` 文件路径 | `Sent_2025_Q3.mbox` |
| `--sender` | 仅统计指定发件人发送的邮件 | `--sender paghegest@gmail.com` |
| `--format` | 输出格式，可选 `csv`、`json`、`text` | `--format csv` |
| `--output` | 输出文件名 | `--output result_v9.csv` |

### 3. 示例
```bash
python gmail_stats_final_v9.py Sent_2025_Q3.mbox --sender paghegest@gmail.com --format csv --output result_v9.csv
```
执行后会在当前目录生成：
```
result_v9.csv
```

---

## 📊 输出格式说明

| 列名 | 含义 |
|------|------|
| `company` | 提取到的公司名（如 `BEAUTY NAILS DI LIN YING 20412`） |
| `employee` | 提取到的员工姓名（如 `ZHU MIMIAO`） |
| `operation` | 员工对应的操作类型（如 `ASSUNZIONE`、`PROROGA` 等） |
| `count` | 统计次数（目前每行对应一条记录） |

示例输出：
```csv
company,employee,operation,count
BEAUTY NAILS DI LIN YING 20412,,TOTAL_MESSAGES,1
BEAUTY NAILS DI LIN YING 20412,ZHU MIMIAO,DIMISSIONE CLIC LAVORO,1
HM TREVISO 20093,ARAUJO NARDOTO REBECA CRISTINA,PROROGA,1
STAR BEAUTY DI LIN 20566,FAROOQ UMAR,VARIAZIONE,1
```

---

## 🔍 正则与提取逻辑说明

### 公司名提取
- 关键字：`DITTA`
- 结束条件：遇到 `->`、`(`、`[`、`dipendente`、`DAL` 等词即停止。
- 合法字符：`A–Z 0–9 & ' - /`
- 示例：
  ```
  Subject: 1 ASSUNZIONE DITTA LU & YAN 20513 DAL 01/04
  → 提取公司名：LU & YAN 20513
  ```

### 员工名提取
- 关键字：`dipendente`
- 向后最多读取 600 个字符；
- 连续大写单词或 Title Case 形式视为姓名；
- 遇到 `/` 或日期模式立即停止；
- 示例：
  ```
  dipendente FAROOQ UMAR 01/01/1995
  → 提取员工名：FAROOQ UMAR
  ```

### 操作状态识别
支持并自动归一化以下类型（大小写均可）：
- **DIMISSIONE CLIC LAVORO**
- **DIMISSIONE**
- **PROROGA**
- **VARIAZIONE**
- **ASSUNZIONE**
- **LICENZIAMENTO**

---

## 🧠 调试建议
- 若运行时遇到 `UnicodeDecodeError`，可检查 `.mbox` 是否 UTF-8 格式。
- 若结果为空：
  - 确认主题中存在 “DITTA”；  
  - 检查发件人筛选条件是否过严（可先不加 `--sender` 测试）。
- 若输出未包含员工名，建议：
  - 搜索 `dipendente` 关键字是否换行；
  - 确认日期格式没有误被识别为姓名一部分（v9 已修复此问题）。

---

## 📦 输出文件
默认输出：
```
result_v9.csv
```
或根据 `--output` 参数自定义文件名。

---

## 🪪 作者与版权
**作者：** 殷明    
**邮箱：** 1500692431ym@gmail.com  
**许可证：** MIT License（自由使用与修改）
