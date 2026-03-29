# 数据读取与分析指南

> READ 路径的参考。使用“xlsx_reader.py”进行结构发现和数据质量审核，
> 然后使用 pandas 进行自定义分析。 **切勿修改源文件。**

---

## 何时使用此路径

用户要求阅读、分析、查看、总结、提取或回答有关 Excel/CSV 文件内容的问题，
无需修改文件。如果需要修改，请移交给“edit.md”。

---

## 工作流程

### 步骤 1 — 结构发现

首先运行“xlsx_reader.py”。它处理格式检测、编码回退、结构探索和数据质量审计：```bash
python3 SKILL_DIR/scripts/xlsx_reader.py input.xlsx                 # full report
python3 SKILL_DIR/scripts/xlsx_reader.py input.xlsx --sheet Sales   # single sheet
python3 SKILL_DIR/scripts/xlsx_reader.py input.xlsx --quality       # quality audit only
python3 SKILL_DIR/scripts/xlsx_reader.py input.xlsx --json          # machine-readable
```支持的格式：`.xlsx`、`.xlsm`、`.csv`、`.tsv`。该脚本尝试对 CSV 进行多种编码（utf-8-sig、gbk、utf-8、latin-1）。

### 步骤 2 — 使用 pandas 进行自定义分析

加载数据并执行用户请求的分析：```python
import pandas as pd
df = pd.read_excel("input.xlsx", sheet_name=None)  # dict of all sheets
# For CSV: pd.read_csv("input.csv")
```**标头处理**（当默认的 `header=0` 不起作用时）：

|情况|代码|
|------------|------|
|第 3 行标题 | `pd.read_excel(路径，标题=2)` |
|多级合并标题 | `pd.read_excel(路径, header=[0, 1])` |
|没有标题 | `pd.read_excel(路径，标题=无)` |

**分析快速参考：**

|场景|图案|
|----------|---------|
|描述性统计 | `df.describe()` 或 `df['Col'].agg(['sum', 'mean', 'min', 'max'])` |
|群组聚合| `df.groupby('地区')['收入'].agg(Total='sum', Avg='mean')` |
|前 N | `df.groupby('地区')['收入'].sum().sort_values(ascending=False).head(5)` |
|数据透视表| `df.pivot_table(values='收入', index='地区', columns='季度', aggfunc='sum', margins=True)` |
|时间序列 | `df.set_index(pd.to_datetime(df['Date'])).resample('ME')['Revenue'].sum()` |
|跨表合并 | `pd.merge(销售，客户，on='CustomerID', how='left', validate='m:1')` |
|堆栈表| `pd.concat([df.assign(Source=name) for name, df in Sheets.items()],ignore_index=True)` |
|大文件 (>50MB) | `pd.read_excel(path, usecols=['Date', 'Revenue'])` 或 `pd.read_csv(path, chunksize=10000)` |

### 步骤 3 — 输出

如果用户指定输出文件路径，则将结果写入其中（最高优先级）。报告格式如下：```
## Analysis Report: {filename}
### File Overview     — format, sheets, row counts
### Data Quality      — nulls, duplicates, mixed types (or "no issues")
### Key Findings      — direct answer to the user's question
### Additional Notes  — formula NaN, encoding issues, caveats
```**数字显示**：货币“1,234,567.89”，百分比“12.3%”，倍数“8.5x”，按整数计数。

---

## 常见陷阱

|陷阱|原因 |修复 |
|--------|--------|-----|
|公式单元格读作 NaN |新生成的文件中的 `<v>` 缓存为空 |通知用户；建议在Excel中打开并重新保存；或使用 `libreoffice_recalc.py` |
| CSV 编码错误 |中文Windows导出使用GBK | `xlsx_reader.py` 自动尝试多种编码；手动指定是否全部失败 |
|列中的混合类型 |列同时包含数字和文本（例如“N/A”）| `pd.to_numeric(df['Col'], error='coerce')` — 报告不可转换的行 |
|年份显示为 2,024 |应用于年份的千位分隔符格式 | `df['年份'].astype(int).astype(str)` |
|多级标题 |两行标题合并 | `pd.read_excel(path, header=[0, 1])`，然后用 `' - '.join()` 展平 |
|行号不匹配| pandas 0 索引与 Excel 1 索引 | `excel_row = pandas_index + 2`（+1 表示 1 索引，+1 表示标题）|

**关键**：切勿先使用“data_only=True”然后使用“save()”打开——这会永久破坏所有公式。

---

## 禁止事项

- 切勿修改源文件（无“save()”，无 XML 编辑）
- 切勿将公式 NaN 报告为“数据为零” - 解释这是公式缓存问题
- 切勿将 pandas 索引报告为 Excel 行号
- 切勿在没有数据支持的情况下做出推测性结论