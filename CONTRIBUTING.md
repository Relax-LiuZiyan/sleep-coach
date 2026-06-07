# Contributing to Sleep Coach

感谢你愿意参与这个项目。

Sleep Coach 不是一个普通的纯界面练手项目，它会涉及真实的系统行为，例如自动关机和开机自启。所以在提 Issue、提 Pull Request 或本地调试时，请优先保证安全和可复现性。

## 提交 Issue 前

请尽量提供以下信息：

- Windows 版本
- Python 版本
- 安装依赖的方式
- 启动方式，是 `python run.py` 还是双击 `launch_sleep_coach.pyw`
- 是否启用了 `SLEEP_COACH_SUPPRESS_SHUTDOWN`
- 复现步骤
- 实际结果
- 预期结果

如果有报错日志，也欢迎附上：

```text
C:\Users\<你的用户名>\.sleep-coach\launcher-error.log
```

## 提交 Pull Request 前

请在说明中明确写清楚：

- 这次改动解决了什么问题
- 改动影响哪些模块
- 是否影响提醒、加班、惩罚、自动关机、开机自启、统计逻辑或数据结构
- 你做了哪些本地验证

如果你的改动涉及下列高风险区域，请单独强调：

- `sleep_coach/system.py`
- `sleep_coach/schedule.py`
- `sleep_coach/controller.py`
- `sleep_coach/storage.py`

## 本地开发建议

- 推荐使用虚拟环境
- 推荐用 `python run.py` 启动，便于调试
- 首次测试时，优先禁用真实关机

参考命令：

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:SLEEP_COACH_SUPPRESS_SHUTDOWN="1"
python run.py
```

## 安全提醒

测试真实关机逻辑前，请先确认：

- 重要文件已经保存
- 当前没有高风险后台任务
- 你明确知道程序何时会触发关机

如果只是验证流程，请始终优先使用：

```powershell
$env:SLEEP_COACH_SUPPRESS_SHUTDOWN="1"
```

## 提交内容规范

- 不要提交本地数据库
- 不要提交运行日志
- 不要提交与本次改动无关的 IDE 垃圾文件
- 提交说明尽量简洁明确

## 行为准则

参与本项目即表示你同意遵守 `CODE_OF_CONDUCT.md`。
