# 增量执行入口：先用命令，不重写脚本

适用：已冻结的同轴球面单片/双胶合、已有API/机械配方/原生STEP证据，采用本包A4图框。首个适配器从API快照格式档案导入。不是任意ZOS全自动工厂；新拓扑/新模板先适配，不能悄悄套旧面号。此路径不做优化、不改R/CT、不自动安装依赖。

## 每次批次先复制冻结工程

开场与继承答案按[字段说明](fields-and-defaults.md)。每次出图/微调先复制到工作目录`.pdfout`新工程，再运行该副本的脚本。原始输入、上一版及其复核结论保持可回查；不要在旧工程原地改图。

```powershell
$py = 'python'
$skill = '<解压后的skill根目录>'
# 首次：复制两个主输入、skill脚本与模板；额外参考用 --dependency 文件或目录
& $py -X utf8 "$skill\scripts\freeze_project.py" --workdir '<工作目录>' --source '<design.zos>' --mechanical '<mechanical.json>' --font '<字体文件>' --label initial
# 上条返回 batch。后续使用冻结副本，不继续调用可变的安装目录脚本。
$batch = '<返回的 .pdfout 新工程>'
$ctl = "$batch\skill\scripts\drawctl.py"
& $py -X utf8 "$batch\skill\scripts\freeze_inputs.py" "$batch\inputs\design.zos" "$batch\inputs\mechanical.json" --out "$batch\archive"
& $py -X utf8 $ctl init --archive "$batch\archive" --out "$batch\project" --title '<项目名>'
$project = "$batch\project\project.json"
& $py -X utf8 $ctl build $project
```

上述build用于建档后生成草图，未替代原生CAD、恢复附页与复核。已有档案可先用`--dependency`复制档案，再从副本init。档案包括`data/api_surfaces.json`、`mechanical.json`、`material_optics.json`、`drawing_manifest.json`、一个`source/*_source.zos`及源哈希一致的`review/main_direct_api.json`。脚本允许native/90附页暂为空以便开发，完整交付范围仍按[工序](execution-workflow.md)检查。

增量先复制已有工程及缓存：

```powershell
& $py -X utf8 "$skill\scripts\freeze_project.py" --workdir '<工作目录>' --project '<上一版project.json>' --label label-edit
$batch = '<返回的新工程>'
$ctl = "$batch\skill\scripts\drawctl.py"
$project = "$batch\project\project.json"
```

复制内容含输入、证据、图面配置和缓存；外部文件引用会本地化。脚本/模板/字体哈希相同可继承缓存，变化则按签名失效。字体副本只作本机冻结依赖，不自动进入交付包。`frozen-manifest.json`记录复制时状态，后续配置/产物变化由build-state及复核记录跟踪，不篡改初始清单来掩盖变更。每个新批次重复复制；该批次内部修复无需为每条命令再复制。

## 一处标注修改（常用）

```powershell
& $py -X utf8 $ctl set-layout $project --page 01_L1 --key radius_front_anchor --value '[61,235]'
& $py -X utf8 $ctl plan $project
& $py -X utf8 $ctl build $project
& $py -X utf8 $ctl review-packet $project --pages 01_L1
& $py -X utf8 $ctl contact $project --pages 01_L1
```

`radius_front_anchor`同时移动文字与引线根，不会把箭头从面上拉走。可配置前后R/面号/倒角、胶合面、涂墨、平台引线坐标、CT/ET高度、ETA外置位置、表格及技术要求区域。`set-layout --help`列所有键。坐标单位纸面mm；修改后必须看图，工具不声称自动避碰。

`build`自动跳过未变化页；`--pages`用于有意分批，不会让未更新页混入合订。输入/模板/脚本/字体变化、产物丢失或被改都会使相关页失效。未修改页的内容和mtime保持不变；不用再全目录渲染或新建一套图框。

## 公差或惯例修改

```powershell
& $py -X utf8 $ctl set-spec $project --key tolerances.center_thickness_mm --value 0.15
# 单页例外（获得用户要求后）
& $py -X utf8 $ctl set-spec $project --page 01_L1 --key tolerances.center_thickness_mm --value 0.10
& $py -X utf8 $ctl plan $project
& $py -X utf8 $ctl build $project
```

全局spec修改使当前所有页缓存失效；`center_thickness_mm`是常规/总厚默认，薄片仍使用`thin_center_thickness_mm`，需要一起改变时分别设置。单页显式CT覆盖优先。标签修改不等于像质良率验证，不自动改名义设计。机械配方改变影响子片及胶合图，宜先形成新验证档案，不手改旧snapshot冒充同源证据。

## 复核与PDF

`review-packet`输出两份独立提示及页清单/哈希/源证据；建议按[复核范围](review-and-roundtrip.md#先选择本次复核范围)区分首次与增量，提示聚焦本次变化，避免重新读历史会话。

主线程保存实际代理结论后记录；程序不认证报告内容，禁止创建假报告绕过复核：

```powershell
& $py -X utf8 $ctl record-review $project --reviewer '<真实代理A标识>' --report '<A报告.md>' --pages 01_L1
& $py -X utf8 $ctl record-review $project --reviewer '<真实代理B标识>' --report '<B报告.md>' --pages 01_L1
& $py -X utf8 $ctl pdf $project
& $py -X utf8 $ctl pack $project
```

正式`pdf/pack`要求每个当前主图都有两份匹配当前DXF、PNG及输入指纹的报告；之前未变页的记录继续有效。未评审/工具实验用`pdf --proof`、`pack --proof`，结果进proof_pdf及`PROOF_NOT_RELEASE.zip`，不冒称发布完成。

单页PDF独立缓存，合订按project明确顺序更新。禁止glob目录把旧尾页/试验页塞进还原或PDF。字体覆盖、占位词、DXF audit自动检查；精确A4画布已封装`pdf_export.py`。图纸比例仍需测一条PDF矢量长度；新模板/新比例重新验证。`pack`只装清单内的文件，并做ZIP读回/哈希核对。

## 需要真实Zemax时才调用

```powershell
& $py -X utf8 '<skill>\scripts\zos_read.py' '<源.zos>'
& $py -X utf8 '<skill>\scripts\zos_export.py' '<源.zos>' --out '<原生CAD目录>' --range L1:2:3 --range L2:4:6
& $py -X utf8 '<skill>\scripts\step_section.py' '<assembly.step>' '<剖面.png>' --ocp-path '<已有OCP安装目录>'
```

`zos_read`统一连接/读系统设置/全局矩阵/输出stdout/断开；不写文件，供只读代理。`zos_export`单次连接导出所需全部range、保存API快照；同源同range同脚本且文件未改则完全不连API。两者共用无磁盘锁的命名mutex，失败finally释放；不杀GUI、不再混用互不协调的filelock。STEP原生哑面厚0.001mm，切面工具只读原生实体不造几何。OCP路径是显式参数，兼容Edge/Edge_s实际API差异，不硬编码临时目录。

改变模型时仍需原有光学验证/从图纸回建；这部分不能用标注快路径替代。当前脚本不会自动把未经验证的新ZOS归档成“已验收”。

## 失败时的最短定位

|现象|先看/执行|不要做|
|---|---|---|
|一页标注挤|该页PNG＋set-layout锚点|重跑Zemax/全部8页|
|数字与模型不一致|plan的源/快照哈希及API面号|按截图OCR反写模型|
|无修改仍慢|last-build/last-pdf的rebuilt列表|反复调代理或全量渲染|
|源/快照被改|重新API/光学验收，导入新档案|改哈希假装证据还有效|
|缺中文/符号|字体覆盖＋实际样式及预览|随意把Ø换φ|
|ZOS占用|统一mutex/standalone退出状况|并发抢license或杀无关进程|
|PDF比例差|exact A4、测矢量线长|仅改MediaBox不校正内容|
|代理只读冲突|zos_read仅stdout；主线程存报告|让代理建锁/写审计文件|
|上下文漂移|project＋review/request＋本次changed页|再读数小时对话|

工具版本和依赖变动须重验对应阶段；当前签名跟踪脚本/模板/字体，第三方包升级需重建工作目录并测试，不能沿用旧缓存推定兼容。

已测量的本机量级：8主图DXF/PNG约21s，15页PDF约19s；仅移动一页标注后，DXF/PNG约4s、PDF/合订约2.5s；无变化两阶段合计约0.7s。计时包含进程启动，不包括用户问询与人工/代理复核。这些历史测量只作为量级参考，公开包以自身smoke测试结果为准。
