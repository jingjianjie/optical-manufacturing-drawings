# DWG / DXF 本地操作

这是optical-manufacturing-drawings包内参考，来源见[历史依据](../references/historical-evidence.md)，无需调用外部cad-dwg-dxf skill。光学出图的工程冻结、确认和复核范围采用[主工序](../references/execution-workflow.md)；此文处理CAD工具细节。

目标是交付可继续编辑的 CAD 文件，文字、几何和单位保真。默认处理副本；原图作为回查依据。按用户任务选用下面的路径，不必执行全部流程。

## 快速入口

- 首次使用或转换 DWG：读 [工具链](references/toolchain.md)。优先已有原生 CAD／ODA；本技能提供 ACadSharp 转换桥和 ezdxf 操作工具。
- 中文、符号、字体替换或任何含文字的交付：读 [中文字体](references/chinese-fonts.md)。字体文件存在不代表覆盖所需字符；渲染器成功退出不代表没有跳过文字。
- 提取图框、分图或生成 DWT：读 [图框与模板](references/frames.md)。图层名只是线索，不能替代实体位置和图形检查。

脚本目录相对本文件。Python 使用 `-X utf8`。参数使用实际路径，不把示例路径当成固定输入。

```powershell
python -X utf8 scripts/cad.py inspect input.dxf --out inventory.json
python -X utf8 scripts/cad.py font-check input.dxf <选定字体文件> --out glyphs.json
python -X utf8 scripts/cad.py unicode-copy legacy.dxf unicode-working.dxf
python -X utf8 scripts/cad.py render input.dxf preview.png --layout Model
dotnet run --project scripts/CadBridge -- input.dwg working.dxf
dotnet run --project scripts/CadBridge -- edited.dxf output.dwg
python -X utf8 scripts/cad.py compare edited.dxf readback.dxf --out comparison.json
```

`font-check` 对整图字符集做候选字体预检，**不等于每个实体实际使用该字体**。`compare` 检查各布局/块的实体类型、位置/几何、文字、样式和关键表记录；忽略 handle/owner 等重建编号。差异需要解释，不自动宣称转换失败或成功。

`unicode-copy` 用于已确认出现字面 `\U+xxxx` 的文本 DXF，创建 R2010 或更高版本 UTF-8 副本；它会解码文件内标准 DXF Unicode 转义。先检查原文，若图纸有故意显示这些字面字符的说明文字，则逐对象处理，不做全文件解码。新建含中文的图纸优先 R2010+，只有兼容性要求才降版并验证。

## 工作闭环

1. 检查文件头、格式版本、模型空间/布局、单位、块/外参、实体类型和文字样式。选择能覆盖实际实体的工具；发现代理实体、动态块、AEC 对象、复杂标注时，优先原生 CAD/ODA 保真。
2. 建立总览和必要的局部图，明确修改对象。修改文字内容、字体和几何是不同操作，分别记录。保留原始格式码、上下标、符号与公差语义；只在用户要求重排的范围重建文字。
3. 在副本做编辑。跨文档复制要处理块、样式、线型等依赖。二维提取也要检查实体 Z、块变换和纸空间视口。读取失败时报告具体对象/格式，不以静默删除使文件能打开。
4. 输出后重新读取；DWG 转回 DXF 检查。确认相关实体、文字、几何、单位和样式保持预期，并对最后交付文件的回读版本渲染。检查中文、工程符号、表格换行/溢出及标注。
5. 交付原生或交换文件、预览及必要的字体映射/转换说明。说明验证级别：数据回读、预览目检、原生 CAD 实开。没有做过的验证不写成通过。

## 边界

- DXF 由 ezdxf 操作；它不直接解析 DWG。改扩展名不构成格式转换。
- 检测到 `$INSUNITS` 为 0 时保持未知，先从已知尺寸验证；不因外框像 A4 就缩放整个设计。
- 不把字体轮廓化作为默认修复，它会丢失文字可编辑性。若用户需要跨机器固定外观，可额外提供轮廓或 PDF 版本，并保留文字版。
- 这套开源工具已验证普通二维线条、多段线和中文 MTEXT；其他对象依其转换通知和回读结果判断，不推广成全 DWG 无损支持。
