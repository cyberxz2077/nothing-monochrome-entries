# Nothing 单色图标入口

[English](README.md)

单独重绘几个与 Nothing 桌面不协调的应用图标，让其它图标继续保持原来的 Nothing 风格。仓库包含可复用的 AI Skill，以及提取图标、构建入口和通过 USB 安装的本地工具。

每个新图标对应一个**独立安装的小型应用**，点击后打开原应用，图标的深浅色由 Nothing 桌面处理。原应用和官方 Nothing 图标包保持不变。

**USB 只用于前期设置。** 安装完成后可以拔线、关闭 USB 调试。入口不需要 Root、无障碍服务、额外的应用权限或后台常驻。本项目与 Nothing 官方无隶属关系。

## 图标如何跟随系统主题

安卓的自适应图标可以包含两类用途不同的素材。

- **前景层和背景层**，方便桌面将彩色图标统一裁成圆形、圆角方形等形状。
- 额外的**单色图层**，技术名称是 `monochrome`，给支持主题图标的桌面提供一份可以重新着色的图形。

一个应用可能已经做好前景和背景，却没有提供可选的单色图层。有些系统也会自动生成主题图标，但转换后仍可能保留杂乱细节或不协调的比例。缺少这一可选图层，不能直接等同于违反安卓的基础图标规范。参见 [Android 官方说明](https://developer.android.com/develop/ui/compose/system/icon_design_adaptive)。

我们的入口提供一份经过重绘的单色图形。选择**系统原生 Nothing 主题图标**后，着色和深浅色切换都由桌面负责，入口自身无需监听主题变化或保持后台运行。另选第三方图标包可能绕过这条原生处理路径；[原理与验证说明](skills/nothing-monochrome-entries/references/validation.md)记录了此前图标包实验与方案选择。

## 点击后怎样打开原应用

入口让安卓打开原应用的启动组件，随后立即结束自己的 Activity。它使用安卓的 [`Theme.NoDisplay`](https://developer.android.com/reference/android/R.style#Theme_NoDisplay)，没有自己的界面可供显示，也不会作为独立页面留在最近任务或返回路径里。

在最初测试的手机上，这样打开应用没有额外的中转页面或闪屏。原应用自己的加载画面和系统正常的启动动画仍可能出现，入口转发也不会消除原应用的启动耗时。实现代码见 [MainActivity.java](skills/nothing-monochrome-entries/assets/MainActivity.java)。

## 与图标快捷方式的区别

许多图标定制工具创建的是**固定快捷方式**，桌面可能在图标上叠加一个小脚标，用来标识创建它的应用。这里的入口属于正常安装的应用，不会经过同一个快捷方式所属应用脚标机制。[AOSP Launcher3 的快捷方式处理代码](https://android.googlesource.com/platform/packages/apps/Launcher3/+/cc1dad0cae1547c3aad40af8676d9e5312e4564b/src/com/android/launcher3/icons/IconCache.java)可以看到这种区别。

代价是应用列表里多一个应用。原应用仍需保留，它的通知圆点或数量、长按快捷菜单、动态图标和应用信息页不会自动转移到新入口。工作资料标识属于另一套机制，仍可能显示。

## 通过 AI 开始使用

克隆仓库，把 `skills/nothing-monochrome-entries` 复制到 AI 工具的 Skill 目录。Codex 通常使用 `~/.codex/skills/`；若已有同名 Skill，先检查、合并再替换文件。

可以这样告诉 AI。

> 使用 $nothing-monochrome-entries，给我选中的几个应用重绘图标，生成能够跟随 Nothing 深浅色主题的入口。保留其它图标，先检查 USB 连接并尝试提取原图。

实际流程如下。

1. 手机先开启**开发者选项**，再开启 **USB 调试**。通过支持传输数据的线缆连接，解锁并授权这台电脑。确认 `adb devices -l` 显示 `device`。
2. 让 AI 识别所选应用及其准确的启动组件，再通过 USB 提取图标。工具支持应用声明的位图和直接引用的自适应前景；无法还原矢量或嵌套资源时，用截图补齐。
3. 用可用的图像工具重绘，也可以提供自己的素材。保留识别特征，简化细节，对照现有 Nothing 图标调整笔画、留白和大小，先确认样本再安装。
4. 使用官方 Android 工具构建、签名独立入口，保留签名文件供以后更新。
5. 安装后继续选择原生 Nothing 主题图标，将新入口放到桌面。检查它能否打开正确应用，以及无需重选图标包就能完成浅→深、深→浅变化。

AI 需要本地文件和命令执行能力，重绘需要图像工具。USB 授权和样本确认由使用者完成。[设置指南](skills/nothing-monochrome-entries/references/setup.md)包含工具与命令，[重绘规范](skills/nothing-monochrome-entries/references/artwork.md)说明图形处理要求。

## 直接运行脚本

需要 Python 3.10+、Pillow、JDK 17、Android SDK Platform 36 和 Build Tools 36.0.0。先按设置指南准备环境；可以复用已有 SDK 和 JDK。

```sh
python -m pip install -r requirements.txt
TOOL=skills/nothing-monochrome-entries/scripts/icons.py
python "$TOOL" --help
python "$TOOL" doctor
python "$TOOL" init-key --signing-dir .local/signing
python "$TOOL" build --config work/myapp.json --signing-dir .local/signing --out out
```

设置 `JAVA_HOME` 和 `ANDROID_HOME`，或通过参数指定路径。配置格式、`extract` 提取命令和 `install` 安装命令见设置指南。构建不会自动安装，安装不会自动切换主题或打开原应用。

将 `.local/signing` 私密备份。更新时保留入口的包名和签名，提高版本号；如果原应用更换了启动组件，重新识别并构建入口。

## 已验证的范围

最初的原型用于 **CMF Phone 1（A015）、Android 16、Nothing OS 4.1、Nothing Launcher 4.0.20**。四个入口已安装，并根据用户在手机上的反馈调整图形；用户认可了原生主题变化与启动体验。

公开的通用工具在 macOS 上通过了单元测试、真机图标提取、构建签名和编译资源检查。它新生成的测试入口**没有另行安装到手机上**，所以公开工具的安装命令仍需单独完成端到端验证。其它手机、桌面版本、Windows 和 Linux 也需要测试；最低 SDK 33 声明不代表已在 Android 13–15 上验证。

具体证据见[验证记录](docs/validation.md)，自己的手机可参照[验收步骤](skills/nothing-monochrome-entries/references/validation.md)。本地测试命令为 `python -m unittest discover -s tests -v`。

## 开源范围与许可

仓库发布源码和操作流程。签名密钥、密码、提取的 APK、个人配置和构建产物保留在本地并排除在 Git 之外，不分发官方 APK、品牌图案集合或已签名的成品入口。

代码和文档采用 MIT License。第三方名称与图案仍归原权利人；本项目开发与文档由 AI 辅助，设计方向、迭代意见与手机体验反馈来自用户。
