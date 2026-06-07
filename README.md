# Sleep Coach

一个面向 Windows 的睡眠督促桌面应用。它通过倒计时提醒、顶部悬浮条、全屏强提醒、临时加班额度、取消惩罚和自动关机流程，帮助用户尽量按计划结束当天活动并准备休息。

![Sleep Coach Logo](sleep_coach/assets/sleep_coach.png)

> [!WARNING]
> 这个程序在达到设定条件后可能触发 Windows 真实关机。
> 第一次体验前，请先阅读本文的“安全测试”和“风险与注意事项”章节。

## 项目简介

Sleep Coach 是一个本地运行的 Windows 桌面应用，适合希望减少夜间拖延、建立稳定休息节奏的个人用户。

项目当前基于 Python 和 PySide6 构建，所有数据默认保存在本机，不依赖云端服务，也不会要求登录账号。

## 核心功能

- 顶部悬浮条显示当前阶段、时间和倒计时。
- 主界面展示今晚计划、执行状态、连续完成天数和最近统计。
- 到达提醒时段后，程序会进入更强的提醒阶段。
- 到达关机时段后，程序会进入全屏强提醒，并可继续触发真实关机。
- 支持申请有限次数的临时加班额度。
- 取消关机会进入惩罚等待阶段。
- 支持收藏提示语句。
- 支持开机自动启动。
- 所有记录和设置默认保存在本地 SQLite 数据库中。

## 适用平台

- 当前仅支持 Windows。
- 项目设计目标是桌面环境，不适用于 Linux、macOS 或移动端。
- 项目目前不是安装包形式，默认以源码方式运行。

## 预装环境

在开始前，请先确保你的电脑已经具备以下环境：

- Python 3.11 或更高版本
- `pip`，通常会随 Python 一起安装
- 正常可用的 Windows 桌面环境

可以先用下面的命令检查环境：

```powershell
python --version
pip --version
```

如果命令无法执行，请先安装或修复 Python 环境，再继续下面的步骤。

## 快速开始

### 1. 克隆仓库

```powershell
git clone https://github.com/Relax-LiuZiyan/sleep-coach.git
cd sleep-coach
```

### 2. 可选：创建虚拟环境

推荐这样做，避免污染系统 Python：

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. 安装依赖

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. 启动程序

命令行启动：

```powershell
python run.py
```

双击启动：

- 直接双击项目根目录下的 `launch_sleep_coach.pyw`

说明：

- `run.py` 适合开发、调试和手动运行。
- `launch_sleep_coach.pyw` 不会弹出终端窗口，更适合日常使用。

## 给普通用户的安装方式

如果你不想自己安装 Python 和依赖库，推荐直接使用 GitHub Releases 里的 Windows 安装包：

- 进入仓库的 `Releases` 页面
- 下载 `SleepCoach-Setup.exe`
- 双击安装
- 安装完成后从开始菜单或桌面快捷方式启动

这类安装包适合普通用户，不需要手动配置 Python 环境。

## 首次使用建议

第一次体验时，强烈建议先禁用真实关机，确认程序行为符合你的预期后，再恢复默认行为。

在当前 PowerShell 会话中这样启动：

```powershell
$env:SLEEP_COACH_SUPPRESS_SHUTDOWN="1"
python run.py
```

如果你想恢复真实关机，可以关闭这个终端窗口，或者手动清掉环境变量后再重新启动程序：

```powershell
Remove-Item Env:SLEEP_COACH_SUPPRESS_SHUTDOWN
```

## 启动方式与日常使用

程序启动后通常会出现以下几个可见部分：

- 主窗口：查看今晚状态、规则、统计和按钮操作。
- 顶部悬浮条：显示当前阶段和剩余时间。
- 系统托盘图标：单击可打开主界面，也可以从托盘菜单里执行“立即休息”或退出。

需要注意：

- 关闭主窗口时，程序默认不会真正退出，而是最小化到系统托盘继续运行。
- 如果你需要彻底退出，请使用托盘菜单中的退出选项。

## 默认规则

当前默认规则如下：

- 工作日提醒时间：`23:10`
- 工作日关机时间：`23:15`
- 周末提醒时间：`23:30`
- 周末最晚关机时间：`00:00`
- 全屏强提醒默认持续：`60` 秒
- 取消后的惩罚等待默认持续：`45` 秒
- 单次临时加班默认时长：`45` 分钟
- 每周临时加班默认上限：`2` 次

跨夜规则：

- `00:00 - 04:59` 仍按“前一晚”计算
- `05:00` 之后才进入新的一天

周末判定规则：

- 周末规则只用于周五晚和周六晚
- 也就是说，代码中的“weekend”并不是整个自然周末白天，而是晚间作息规则的特殊窗口

## 配置说明

程序支持两类配置：时间计划和执行策略。

### 时间计划

包括：

- 工作日提醒时间
- 工作日关机时间
- 周末提醒时间
- 周末关机时间

当前实现里，这部分修改更偏向“调整今晚安排”：

- 你需要先通过 30 秒的确认门槛，才能修改时间
- 时间修改保存后，会作为“今天/今晚”的日程覆盖值写入本地数据库
- 它更适合临时调整今晚，而不是把全局默认时间永久改写

### 执行策略

包括：

- 全屏强提醒秒数
- 惩罚等待秒数
- 单次临时加班分钟数
- 每周临时加班上限
- 是否开机自启
- 顶部悬浮条是否始终置顶

这部分设置会保存为全局设置，供后续启动继续使用。

## 数据保存位置

程序默认会在当前 Windows 用户目录下创建本地数据目录：

```text
C:\Users\<你的用户名>\.sleep-coach\
```

其中主要文件包括：

- 本地数据库：`C:\Users\<你的用户名>\.sleep-coach\sleep_coach.db`
- 启动异常日志：`C:\Users\<你的用户名>\.sleep-coach\launcher-error.log`

数据库中主要保存：

- 应用设置
- 每日睡眠记录
- 提示语句及收藏状态
- 当晚规则覆盖值

## 开机自启说明

程序支持开机自启，而且默认设置为开启。

启用后，程序会在当前用户的 Windows Startup 目录下写入启动脚本：

```text
C:\Users\<你的用户名>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\sleep-coach.cmd
```

这个脚本会在开机后调用 Python 启动 `run.py`。

如果你不希望程序随系统启动，请在应用设置里关闭“开机自动运行”。

## 风险与注意事项

这是本项目最重要的部分，请在长期使用前认真阅读。

### 1. 真实关机风险

当程序进入相应流程后，会调用 Windows 的关机命令：

```powershell
shutdown /s /t 0
```

这意味着：

- 未保存的文档可能丢失
- 正在运行的程序可能被强制关闭
- 如果你在调试或演示，请务必先启用 `SLEEP_COACH_SUPPRESS_SHUTDOWN=1`

### 2. 开机自启风险

程序默认可能在你忘记的情况下随开机自动运行。如果你暂时不想使用，请主动检查并关闭开机自启设置。

### 3. 配置不当的风险

如果你把提醒时间或关机时间设置得过早，程序会严格执行相应阶段。请先在安全测试模式下熟悉行为，再投入日常使用。

### 4. 平台限制

这个项目当前只针对 Windows 开发和验证。其他系统即使能够运行部分 Python 代码，也不代表行为正确，尤其是托盘、窗口和关机逻辑。

## 安全测试

如果你只是第一次试用，推荐按下面的顺序测试：

1. 打开 PowerShell
2. 进入项目目录
3. 设置禁用真实关机的环境变量
4. 启动程序
5. 手动调整时间，观察提醒、全屏和托盘行为

参考命令：

```powershell
cd D:\sleep
$env:SLEEP_COACH_SUPPRESS_SHUTDOWN="1"
python run.py
```

测试重点建议：

- 先确认主界面能打开
- 先确认关闭窗口后是否仍在托盘运行
- 先确认加班、取消、立即休息这几个按钮的行为
- 等你完全理解流程后，再考虑去掉环境变量测试真实关机

## 常见问题

### 1. 为什么我关闭窗口后程序还在运行？

因为当前设计是“关闭主窗口等于最小化到托盘”，不是完全退出。请从系统托盘菜单里退出。

### 2. 为什么程序会自动关机？

这是项目的核心机制之一。到达设定阶段后，程序会根据规则进入强提醒或关机流程。

### 3. 为什么周末最晚不能超过 `00:00`？

这是当前产品规则的一部分。代码层面也对这一点做了限制，超过 `00:00` 会被拒绝。

### 4. 为什么我改了时间，但感觉不像永久生效？

因为当前实现中的时间修改更像“覆盖今晚安排”，而不是永久改写默认的全局时间模板。

### 5. 如果启动失败怎么办？

先检查：

- Python 是否安装正确
- 依赖是否已安装
- 是否能正常导入 `PySide6`
- 本地日志文件是否生成：`C:\Users\<你的用户名>\.sleep-coach\launcher-error.log`

## 项目结构

```text
sleep-coach/
├── sleep_coach/
│   ├── assets/
│   ├── ui/
│   ├── app.py
│   ├── controller.py
│   ├── models.py
│   ├── quotes.py
│   ├── schedule.py
│   ├── storage.py
│   └── system.py
├── launch_sleep_coach.pyw
├── run.py
├── requirements.txt
└── README.md
```

## 面向开发者的说明

如果你打算继续开发或修改这个项目，建议先注意下面几点：

- 所有系统行为里，最敏感的是自动关机和开机自启
- 规则时间、跨夜判断、周末定义和统计逻辑都集中在核心模块里
- 修改这类逻辑前，最好先在禁用真实关机的模式下验证
- 不要把你的本地数据库、日志或个人运行数据提交到仓库

## 构建 Windows 安装包

项目已经内置了基于 `PyInstaller + Inno Setup` 的打包流程，适合后续继续复用。

### 打包前准备

- 安装 Python 依赖
- 安装 `PyInstaller`
- 安装 `Inno Setup 6`

### 一键构建

在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-release.ps1
```

构建完成后，主要产物位置如下：

- 可运行目录版：`dist\SleepCoach\`
- 免安装压缩包：`release\SleepCoach-portable.zip`
- Windows 安装包：`release\SleepCoach-Setup.exe`

### 相关文件

- `SleepCoach.spec`：PyInstaller 配置
- `installer\SleepCoach.iss`：Inno Setup 安装器脚本
- `scripts\build-release.ps1`：一键构建脚本
- `.github/workflows/release.yml`：GitHub Actions 自动构建与发布流程

### 自动发布

仓库已经配置好 GitHub Actions：

- 当你推送类似 `v0.1.1`、`v0.2.0` 这样的标签时
- GitHub 会自动在 Windows runner 上构建安装包和便携版
- 并把它们上传到对应的 GitHub Release

更多协作细节请阅读 `CONTRIBUTING.md`。

## 贡献

欢迎通过 Issue 和 Pull Request 参与改进。

在提交改动前，请先阅读：

- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`

## License

本项目基于 `MIT License` 开源，详见 `LICENSE`。
