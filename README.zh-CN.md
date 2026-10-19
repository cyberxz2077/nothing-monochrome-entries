# Nothing 单色图标入口

[English](README.md)

把少量未适配的应用图标重绘成与 Nothing 桌面协调的单色图案，同时保留其它应用的原生风格。仓库包含可复用的 AI Skill 和可执行的本地工具。

实现方式是给每个应用生成一个独立的小型 APK：提供带 `monochrome` 图层的普通应用入口，点击后打开原应用并立即结束。**深浅色由 Nothing 桌面处理；USB 调试只用于读取应用和安装，完成后可以拔线、关闭调试。**

不需要 root、无障碍服务、常驻后台或额外权限。不会修改官方 Nothing 包，也不会替换原应用。本项目与 Nothing 官方无隶属关系。

## 完整流程

1. 手机开启开发者选项，再开启 USB 调试；通过数据线连接，解锁并允许这台电脑的 RSA 调试授权。
2. 确认 `adb devices -l` 显示 `device`，识别目标应用准确的包名和启动组件/别名。
3. 优先从安装包提取声明的图标位图；自适应图标可继续提取直接引用的前景图层。复杂矢量或嵌套 XML 无法直接还原时，使用截图补齐。
4. 用可用的 AI 图像工具按原图重绘；保留识别特征，调整笔画、负空间、比例、光学位置，在小尺寸下检查。也可以直接提供自己的素材。
5. 用官方 Android 工具构建、签名入口，保存本地签名身份，以后可以原位更新。
6. 安装后选择**系统原生 Nothing 图标模式**，检查点击打开原应用，以及深→浅、浅→深自动变化。

AI 需要本地文件/命令能力；重绘需要图像工具。手机授权和视觉确认仍由使用者参与，并非连接任意聊天机器人就能全自动完成。

## 安装 Skill

把 `skills/nothing-monochrome-entries` 目录复制到 AI 工具的 Skill 目录。Codex 通常使用 `~/.codex/skills/`；若已有同名目录，先检查再合并。

可这样调用：

> 使用 $nothing-monochrome-entries，给我选中的几个应用重绘图标并生成支持原生 Nothing 深浅色的入口。保留其它图标，先检查 USB 连接并尝试提取原图。

- [连接前置顺序、工具链、命令与配置](skills/nothing-monochrome-entries/references/setup.md)
- [图标重绘规范与迭代方法](skills/nothing-monochrome-entries/references/artwork.md)
- [原理、验收与脚标差异](skills/nothing-monochrome-entries/references/validation.md)

也可以直接运行 `scripts/icons.py`，见 [English README](README.md) 的命令示例。需要 Python 3.10+、Pillow、JDK 17、Android SDK Platform 36 与 Build Tools 36.0.0；构建和安装是明确分开的操作。

## 与快捷方式的区别

许多图标定制工具创建的是固定快捷方式，桌面可能叠加其所属应用的小脚标。这里安装的是独立应用的正常 Launcher Activity，因此不会走同一个快捷方式所属应用脚标路径。通知圆点、工作资料标识是另外的机制，不能笼统保证所有桌面上都没有任何标记。

代价是应用列表多一个入口。原应用仍保留；它的通知角标、长按菜单、动态图标及应用信息页不会自动继承。入口更新需要保持同一包名与签名，签名文件必须妥善备份。

原始实践在 A015 / Android 16 / Nothing OS 4.1 / Nothing Launcher 4.0.20 上得到用户认可；其它版本需要实测。公开工具的验证范围见 [验证记录](docs/validation.md)。仓库只包含源码和流程，不分发官方 APK、第三方图标包、个人签名、设备日志或品牌图案集合。

代码和文档采用 MIT License。第三方名称与图案仍归原权利人；本项目开发与文档由 AI 辅助，设计方向、迭代意见与手机体验反馈来自用户。
