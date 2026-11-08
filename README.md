# VOCALOID6-CN

面向 **VOCALOID6 Editor Lite 6.13.3 / 程序集 6.13.3.1** 的简体中文适配工程。

**Windows 桌面端已获用户确认：可以正常使用。** 当前发布为桌面试用版 R1；插件宿主、各 DPI 布局和逐项功能验收仍在进行。

## 已有成果

- 编辑器与插件的独立 `zh-CN` 中文资源程序集。
- 733 个中文资源键，附中英日对照词库及音乐制作术语表。
- 保留原主体文件，通过专用启动器加载中文资源。
- 独立副本安装、补丁卸载与原版界面恢复工具。
- 可构建的 .NET 8 工程、资源检查脚本与测试记录。

日语资源和默认英文资源各有 731 键，其中两处键名不同；中文资源保留并集的 733 键。中文用词参考声库厂商资料、中文 VOCALOID 教程及已有适配，统一使用声库、片段、音素、表情等名称。

## 下载与安装

下载 [桌面试用版 R1](dist/VOCALOID6_CN_Desktop_R1.zip)，解压全部文件。电脑需要已安装原版 VOCALOID6 Lite 6.13.3、可用声库及 .NET 8 Desktop Runtime。

1. 关闭 VOCALOID6 和相关 DAW。
2. 双击 `Install.cmd`，按提示指定原版 Editor 文件夹，即包含 `VOCALOID6.dll` 的目录。交互输入路径时不加引号。
3. 工具会在 `%LOCALAPPDATA%\VOCALOID6-CN-6.13.3-R1` 创建独立副本。
4. 双击副本中的 `Start-Chinese.cmd` 启动中文界面。

安装器复制并核验程序文件，不覆盖原版目录。用户设置、缓存和授权仍由原应用管理；首次测试请使用工程副本。

### 桌面快捷方式与启动失败

不要把 `Start-Chinese.cmd` 本体移出安装副本。它通过自身路径寻找 `VOCALOID6.exe` 和中文适配器。

需要桌面入口时，双击补丁包中的 `Repair-Launcher.cmd`。该工具补回缺失或损坏的中文资源和启动适配器，备份并修复副本的启动脚本、更新卸载校验记录，在实际桌面目录建立 `VOCALOID6 Chinese.lnk`。之后使用该快捷方式启动。

若提示 `Missing installed file: zh-CN\VOCALOID6.resources.dll`，请使用包含 DLL 的 [资源恢复包](dist/VOCALOID6_CN_Resource_Recovery.zip)，解压后运行其中的 `Repair-Launcher.cmd`。

默认修复 `%LOCALAPPDATA%\VOCALOID6-CN-6.13.3-R1`；自定义目录使用：

```bat
Repair-Launcher.cmd -InstallDir "D:\V6-CN-Test"
```

新版启动脚本会把标准输出、错误和退出码写入副本的 `V6CN-launch.log`；启动文件缺失或进程异常退出时保留命令窗口。修复工具另生成 `V6CN-startup-diagnostic.txt`，包含运行中的 VOCALOID6 进程及近期相关应用错误。日志只写在本机，分享前请检查其中的路径和工程名称。

如果软件无响应，先正常关闭已有实例；无法关闭时，保存其他工作后重启 Windows，再运行桌面快捷方式。修复工具不自动结束进程，也不清除用户配置。

### 提示目标文件夹已存在

`Destination already exists` 表示目标目录已有内容。若该目录内有 `Start-Chinese.cmd` 且没有 `V6CN-INCOMPLETE.txt`，可直接启动已有副本。需要重新安装时，在补丁目录中运行：

```bat
Install.cmd "" "%LOCALAPPDATA%\VOCALOID6-CN-6.13.3-Test2"
```

也可指定原版路径与新的目标路径：

```bat
Install.cmd "C:\Program Files\VOCALOID6\Editor" "D:\V6-CN-Test"
```

目标目录必须不存在。`V6CN-INCOMPLETE.txt` 表示安装未完成，需要选择新的目录重新安装。

### 卸载与恢复

双击 `Restore.cmd`，移除副本中的中文资源和启动适配器，保留程序副本、工程及记录。随后启动副本的 `VOCALOID6.exe` 使用原版界面。

自定义安装目录时运行：

```bat
Restore.cmd "D:\V6-CN-Test"
```

## 验证情况

| 项目 | 当前证据 |
| --- | --- |
| Windows 桌面端使用 | 2026-11-09 用户确认可正常使用 |
| 中文资源逐键读回 | 编辑器、插件各 733 键通过 |
| 真实主体的资源访问器 | 编辑器、插件各 731 个通过 |
| 安装与恢复工具 | 12 项检查通过 |
| 原版文件保护 | 独立副本测试中原版全部文件哈希保持一致 |
| 全功能、各 DPI、中文布局 | 待逐项验收 |
| DAW 插件宿主 | 待验证；Lite 自身不支持 VST/AU |

用户的桌面反馈记录在 [Windows 用户验证记录](reports/Windows用户验证.md)。资源探针测试不等于实际插件宿主测试。尚需盘点 BAML 固定文字、参数元数据标签和原生效果器界面，当前版本不标记为全界面汉化完成。

Windows 下可运行 `Probe-Windows.cmd`，再按 [验收清单](reports/Windows验收清单.csv) 检查具体窗口与功能。

## 实现方式

中文卫星资源放在 `zh-CN` 子目录，与原程序集名称、版本及资源基名匹配。原版启动逻辑仅接受日语与英语，专用启动器通过 .NET Startup Hook 将目标副本的生成资源类 `Culture` 属性设为 `zh-CN`。

适配器只作用于指定副本中的 6.13.3.1 编辑器和插件程序集，不改写主体 DLL，不设置全局环境变量，不注册 COM。直接启动原版程序使用原有资源选择方式。

`payload/ja-JP` 是兼容性研究输出，默认安装器不安装它。

## 构建

安装 Python 3.10+ 与 .NET 8 SDK，然后运行：

```sh
python build.py --validate-only
python build.py
```

Windows 也可使用 `Build.cmd`。构建不需要原版主体 DLL。GitHub Actions 提供手动运行的 Windows 构建流程。

原 DLL 提取和完整性核对需另装依赖：

```sh
pip install -r tools/requirements.txt
python tools/extract.py "C:\原版\Editor" extracted
python tools/audit.py "C:\原版\Editor"
```

主要目录：`translations` 保存词库，`src` 保存资源及工具源码，`tools` 保存提取和检查脚本，`payload` 保存当前编译产物，`reports` 保存证据和测试说明。

## 资料与署名

- [术语校准说明](reports/术语校准.md)
- [兼容性与测试报告](reports/兼容性与实机测试报告.md)
- [第三方资料说明](THIRD_PARTY_NOTICES.md)

VOCALOID 及原软件、声库的权利归各自权利人所有。本仓库提供中文适配资源和工具，不包含原版主程序、合成引擎、声库或激活组件。
