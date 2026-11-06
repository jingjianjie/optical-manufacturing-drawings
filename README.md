# Optical Manufacturing Drawings

Self-contained agent skill and Python tools for optical manufacturing DXF/PDF drawings.
MIT licensed source. 中文工作流，English CLI；无需安装其他 agent skill，也不依赖作者的项目目录或历史对话。

## 支持范围

- 离线：同轴球面/平面单片与双胶合、机械平台/倒角、A4中文制造图、符号块、PDF、增量更新与冻结工程。
- 在线：Windows + 已安装且有许可的 OpticStudio + ZOSPy，直接读取处方、材料、原生STEP和采样光线。整体光路图入口已包含在本包。
- 同轴/面型/配置边界见 [能力说明](references/api-alignment.md)。此包不是优化器，也不是任意系统的全自动回建器；复杂偏心、反射、多配置或非球面需要专项适配。

## 离线快速运行（不需要 Zemax）

需要Python 3.10+；建议3.11，新建虚拟环境。使用支持中文和工程符号的本地TTF/OTF/TTC字体，或自行安装Noto Sans CJK；字体不随包分发。

```sh
python -m pip install -r requirements.txt
python scripts/make_example.py --out demo-archive
python scripts/drawctl.py init --archive demo-archive --out demo-project --title DEMO --font /path/to/CJK-font.ttf
python scripts/drawctl.py build demo-project/project.json
python scripts/drawctl.py pdf demo-project/project.json --proof
python scripts/system_layout.py --snapshot demo-archive/source/synthetic_source.json --mechanical demo-archive/data/mechanical.json --out demo-layout.png
```

示例完全合成，含平凸单片、异径双胶合及平台，不是实际处方；输出只作proof，不能解锁制造发布。`tests/smoke.py --font FONT --workdir EMPTY_DIR`可检查离线链、跨目录搬迁、缓存、符号和打印比例。

## 使用真实设计

仓库还提供 [脱敏 ZOS/ZMX 解析样例](samples/README.md)：虚构曲率打乱、面间距归零、材料清空、零视场、孔径直径0.1mm，仅用于读取测试，不是有效设计。它从新系统生成，不含原处方；可用的离线出图示例仍由上面的make_example生成。

在代理中加载 [SKILL.md](SKILL.md)，从[工序](references/execution-workflow.md)进入。原始ZOS和机械JSON作为两个设计输入，图面配置/证据由工程保存。每次出图或增量先创建工作目录`.pdfout/`副本：

```sh
python scripts/freeze_project.py --workdir WORK --source design.zos --mechanical mechanical.json --font FONT --label initial
```

使用返回工程内的skill脚本继续操作。安装在线依赖见 [环境](references/environment.md)。图纸默认值是**示例配置**，项目需采纳或覆盖；并非通用制造标准。公开包不含真实ZOS、客户图纸、旧截图、会话日志或字体。

## 发行和许可证

本包自有源码、文档和生成图框适用[MIT](LICENSE)。外部依赖分别适用其自身许可，见[第三方依赖](THIRD_PARTY.md)；本包不附依赖二进制、Zemax运行时或玻璃库。`scripts/release.py --out DEST.zip`按公开文件白名单打包，区别于包含设计数据的`drawctl pack`。后者输出制造交付包，**不应用来发布开源代码**。
