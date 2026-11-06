# 本地工具链

## 安装与启动

已有可用 Python 环境可直接复用。缺依赖时在任务目录创建 venv，避免改其他项目环境：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install ezdxf==1.4.5 matplotlib==3.7.1 fonttools==4.40.0
dotnet build <skill-dir>\cad\scripts\CadBridge
```

上述 Python 版本组合在 Python 3.11 实测。本桥使用 .NET 8 和 ACadSharp 3.8.35。不同 Python/运行时可采用兼容版本，并复跑真实输入。依赖下载只需程序包，不需要上传图纸。

本地验证范围见 [validation.md](validation.md)。`font-check` 返回 2 表示每个候选 face 都有缺字，`compare` 返回 2 表示存在差异或未覆盖实体类型；这是待审查结果，不一定是程序崩溃。PowerShell 多条命令不要只看最后的退出码。

桥接受 `input.dwg|dxf output.dwg|dxf`，扩展名不区分大小写，输出已存在时拒绝覆盖。它输出转换通知、读取和回读实体数；通知需要 agent 审查。需要不同 DWG 版本、复杂布局或专用对象时，用目标 CAD/ODA 的官方转换能力，不假设本桥覆盖所有版本。

## 操作选择

|任务|路径|
|---|---|
|DWG 读取/编辑|转换副本为 DXF → ezdxf 修改 → 转换回 DWG → 回读|
|DXF 图层/块/实体操作|ezdxf；先 inspect 后读精确对象|
|AutoCAD 原生布局、动态块、打印设置、专有对象|已安装的原生 CAD API/COM/控制台或 ODA；必要时 GUI|
|DWG 无法读取|保留失败信息，尝试另一种本地 reader；不要反复运行同一失败转换|

注册表中存在 AutoCAD ProgID 只说明曾注册；验证实际 EXE 和版本。注册表残留不代表EXE可用。DWG 的 `AC1032` 是 2018 系列文件格式，不是具体创建应用年份。

## LibreDWG 作为读取备选

本次 LibreDWG 0.14 `dwg2dxf` 能读源图；同版本 `dxf2dwg` 产生无效 handle，不能作为本任务的可靠写入器。ACadSharp 3.8.35 写入后回读正常。这是实际文件结果，不代表任一工具永远优于另一工具。

LibreDWG Windows CLI 对本次中文路径读取失败。处理此类旧 CLI 时：在纯 ASCII 路径建立独立临时目录，用 Python/PowerShell 复制输入为 `input.dwg`，执行 argv 参数化调用，最后复制结果回中文目录。不能只改文件名而保留中文父目录。保存 stderr，设置进程超时。Unicode 原生工具无需强制绕行。

官方入口：
- https://github.com/DomCR/ACadSharp
- https://ezdxf.readthedocs.io/
- https://github.com/LibreDWG/libredwg/releases
- https://www.opendesign.com/guestfiles/oda_file_converter

## 保存问题

跨文档导入后的 `$DIMSTYLE` 可能指向不存在的样式，本次出现 `ISO-25` KeyNotFound。先确认所有引用是否存在。无尺寸对象的空框可设为实际存在的 `Standard`；有尺寸对象时恢复正确样式和参数，不能全图覆盖以绕过异常。

`doc.audit()` 可能修复内存对象；脚本只报告而不保存修复。没有 audit 错误也不能证明图形外观、文字和打印效果正确。回读比对中的实体数量相同只是最低门槛。
