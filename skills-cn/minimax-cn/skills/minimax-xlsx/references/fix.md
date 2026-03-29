# FIX — 修复现有 xlsx 中损坏的公式

这是一个编辑任务。您必须保留所有原始表格和数据。切勿创建新的工作簿。

## 工作流程```bash
# Step 1: Identify errors
python3 SKILL_DIR/scripts/formula_check.py input.xlsx --json

# Step 2: Unpack
python3 SKILL_DIR/scripts/xlsx_unpack.py input.xlsx /tmp/xlsx_work/

# Step 3: Fix each broken <f> element in the worksheet XML using the Edit tool
#   (see Error-to-Fix mapping below)

# Step 4: Pack and validate
python3 SKILL_DIR/scripts/xlsx_pack.py /tmp/xlsx_work/ output.xlsx
python3 SKILL_DIR/scripts/formula_check.py output.xlsx
```## 错误修复映射

|错误|修复策略|
|--------|-------------|
| `#DIV/0！` |换行：`IFERROR(original_formula, "-")` |
| `#NAME？` |修复拼写错误的函数（例如“SUMM”→“SUM”）|
| `#REF！` |重建损坏的参考 |
| `#VALUE！` |修复类型不匹配 |

有关 Excel 错误类型和高级诊断的完整列表，请参阅“validate.md”。

## 关键规则

- 输出必须包含与输入相同的工作表。不要创建新的工作簿。
- 仅修改损坏的特定“<f>”元素 - 其他所有内容都必须保持不变。
- 打包后，始终运行“formula_check.py”以确认所有错误均已解决。