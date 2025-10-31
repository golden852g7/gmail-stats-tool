Gmail 邮件统计工具（v2 版）
📦 功能简介

该工具用于分析从 Gmail 导出的 .mbox 邮件文件，统计你发给不同公司的邮件中，涉及各员工的状态变化情况。
支持自动识别公司、员工姓名及 6 种状态类型，并导出成可在 Excel 打开的 CSV 文件。

📤 如何获取 Gmail 邮件的 .mbox 文件

打开 Google Takeout：
👉 https://takeout.google.com/

在导出内容中，仅勾选 「Gmail」 服务。

点击「下一步」，选择导出格式：

文件类型：.zip

频率：一次性导出

文件大小：建议 2GB 或 4GB

点击「创建导出」，等待 Google 打包完成。

⚙️ 只导出已发送邮件（Sent Mail）

点击「包含的邮件标签（All mail data included）」

取消全选，仅勾选 Sent Mail（已发送邮件）

这样导出的文件只包含你发出的邮件。

导出完成后，下载压缩包并解压。你将看到类似结构：

Takeout/Mail/Sent Mail.mbox


这就是可直接用于本工具的 .mbox 文件。

将 .mbox 文件放入与你的脚本（gmail_stats_final_v2.py）相同的目录下。

⚙️ 工具功能说明
✅ 支持识别的状态类型
状态	含义
ASSUNZIONE	新入职
PROROGA	合同续签
VARIAZIONE	合同变更
DIMISSIONE	辞职
DIMISSIONE CLIC LAVORO	工会辞职（与 DIMISSIONE 区分统计）
LICENZIAMENTO	解雇
✅ 自动识别逻辑
项目	规则
公司名称	从邮件主题中提取 “DITTA” 后面的公司名
员工姓名	从正文中提取 “dipendente” 后的全大写英文字符串（遇小写或符号立即停止）
多员工识别	一封邮件中如出现多个 dipendente 段落，会识别多个员工
TOTAL_MESSAGES	按公司统计（每封邮件只算一次）
🧮 使用方法
💻 基本命令（Windows）
python gmail_stats_final_v2.py "Sent Mail.mbox" --format csv --output result.csv


执行后会生成 result.csv 文件，可用 Excel 打开查看。

📅 按日期过滤统计

你可以通过 --start-date 与 --end-date 指定统计时间范围：

python gmail_stats_final_v2.py "Sent Mail.mbox" ^
  --start-date 2025-01-01 ^
  --end-date 2025-10-31 ^
  --format csv ^
  --output result.csv


📘 参数说明：

参数	说明
--start-date	统计起始日期（含当天）
--end-date	统计截止日期（含当天）
--format	输出格式，目前仅支持 csv
--output	输出文件名，默认 result.csv
🧾 输出示例（CSV）
company	employee	operation	count
HM TREVISO		TOTAL_MESSAGES	2
	BAYATI MD HRIDOY	VARIAZIONE	1
	BITTOLO MATTEO	PROROGA	1
	GALLEGOS SALGUERO JEAN CARLOS	PROROGA	1
ACME		TOTAL_MESSAGES	1
	MARIO ROSSI	DIMISSIONE CLIC LAVORO	1

✅ 每个公司只计一次 TOTAL_MESSAGES，
✅ 同一封邮件内的多个员工会单独统计。

🧪 如何使用 demo 文件测试

工具附带测试文件（demo_v2.mbox），你可以用它快速验证运行结果。

示例命令：
python gmail_stats_final_v2.py demo_v2.mbox --format csv --output test_result.csv


然后用 Excel 打开 test_result.csv，应看到上表类似结构。

⚙️ 环境要求

Python ≥ 3.9

无需额外依赖，仅使用标准库：mailbox, re, csv, datetime, argparse
