# 随手账 · 跟夏末做产品 03：Git 与 GitHub 实操

本集用一个真实记账产品练习提交、分支、冲突、撤销、推送、协作、Issue、PR 和固定版本交付。当前产品支持月份导航，并明确区分“正常空月”和“读取失败”。它通过本机后端读写 SQLite，没有账号隔离和云端部署；所有教学金额都是虚构数据。

- 本集仓库：[ledger-git-github-tutorial-v4](https://github.com/xmhuangzhijun-hue/ledger-git-github-tutorial-v4)
- 起点源码：[本课初始提交](https://github.com/xmhuangzhijun-hue/ledger-git-github-tutorial-v4/tree/095b042e45e60c29ad90dde464d1d35d6d9f8e5e)
- 固定完成版：[本集 Releases](https://github.com/xmhuangzhijun-hue/ledger-git-github-tutorial-v4/releases)：选择与视频一致、实际验收通过的版本；`main` 会继续变化。
- 个人博客：[夏末](https://huangzhijun.online/)

## Windows 从新目录运行

准备官方 Python 3.11 或以上，确认终端能运行 `py --version`。在下载或克隆的项目目录打开一个 PowerShell 终端，从头建立本目录自己的虚拟环境：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

首次安装依赖需要网络。直接调用虚拟环境里的 Python，不需要激活环境或改变 PowerShell 执行策略。不要把旧目录的 `.venv` 复制过来并称作“从零安装”。

默认端口为 **8000**：

```powershell
.\.venv\Scripts\python.exe app.py
```

对应地址：<http://127.0.0.1:8000/>。

**本课录制显式使用 8002**，启动命令是：

```powershell
.\.venv\Scripts\python.exe app.py --port 8002
```

对应地址：<http://127.0.0.1:8002/>。两个浏览器都使用同一个端口。端口冲突时先核对占用者；程序不会自动换端口或终止其它服务。`127.0.0.1` 只代表当前电脑，把这个地址发给朋友不能访问你的服务。

服务窗口保持运行，Git 命令在另一终端执行。按 Ctrl+C 正常停止服务后，再换目录运行同一端口；不要同时让两个目录争用 8002。

## 代码和账本是两份东西

- 默认账本位于本项目 `data/ledger.sqlite3`，路径相对于 `app.py`，首次启动会创建空表。
- Git 忽略 `data/`、`.venv/`、`*.sqlite3*` 和 `.env`。公开 `main`、标签和源码包不包含运行时账本数据库；**clone 代码不会复制原账本**。
- 换电脑使用需要另行准备自己的账本数据。本课复现只使用下列四笔虚构记录，不能复制私人账本来演示。
- `legacy.html` 保留旧版比较入口；旧 localStorage 不会自动迁移，不要清理原浏览器数据。

## 固定版本到新目录复验

在 Release 里查看本课实际版本名，克隆时用那个标签；下列 `实际标签名` 必须替换为已发布且经过验收的标签，不能原样输入：

```powershell
git clone --branch 实际标签名 https://github.com/xmhuangzhijun-hue/ledger-git-github-tutorial-v4.git ledger-release-check
Set-Location ledger-release-check
git status
git branch --show-current
git rev-parse HEAD
```

检出固定标签时，Git 可能提示 `detached HEAD`：HEAD 直接指向固定提交，此时分支名为空是预期现象。先把完整提交号与 Release 的目标提交核对。仅验收这个固定版本不需要建分支；若要修改并保留新提交，先运行 `git switch -c practice/from-release`。已有游离提交也应先建分支保住，再切走。

按上文重新创建 `.venv`、安装依赖。新目录没有旧账目是预期结果。可以在页面手动录入下面四笔，也可以在服务停止、目标账本为空时使用教学导入脚本：

| 日期 | 金额（元） | 分类 | 备注 |
|---|---:|---|---|
| 2026-09-15 | 23.00 | 餐饮 | 虚构午饭 |
| 2026-09-16 | 8.00 | 交通 | 虚构公交 |
| 2026-09-17 | 100.00 | 购物 | 虚构购物 |
| 2026-10-01 | 10.00 | 餐饮 | 虚构早餐 |

```powershell
.\.venv\Scripts\python.exe seed_teaching_data.py --db .\data\ledger.sqlite3 --fixture .\teaching-fixture.json
.\.venv\Scripts\python.exe inspect_db.py --db .\data\ledger.sqlite3
$env:LEDGER_DB = (Join-Path (Get-Location) 'data/ledger.sqlite3')
.\.venv\Scripts\python.exe app.py --port 8002
```

导入工具只接受四笔规定的虚构 fixture、整数分金额和有效日期；目标数据库已有任何记录就拒绝，**没有覆盖或清空模式**。不要对正在运行或自己的正式账本执行它。手动录入和工具导入选一种，不能重复导入。

`LEDGER_DB` 只在当前服务终端显式指向新目录的教学账本，避免曾设置过的环境变量让新服务误读旧目录。新目录启动前仍须停止旧目录的 8002 服务，不复制旧数据库。

在 <http://127.0.0.1:8002/> 实际核对：九月 **3 笔 / 131.00 元**，十月 **1 笔 / 10.00 元**；八月是正常空月。保留已加载页面后停止这个服务，点击“重新读取”：应显示读取失败、未知金额/笔数，不能显示“0 元”；失败时切换月份仍应表示失败。重启同一目录、同一数据库、同一端口后重新读取，核对数据恢复且输入仍保留。

另开终端执行已有接口验收脚本：

```powershell
.\.venv\Scripts\python.exe check_api.py --url http://127.0.0.1:8002
```

`inspect_db.py` 通过 Python 自带 `sqlite3` 只读查询，不需要 SQLite CLI。`check_api.py` 发送应被拒绝的输入，检查返回码和原记录不变，不插入正常示例数据。脚本结果不能代替上面的真实页面验收。

若在新目录发现代码或启动说明缺项，回到 A 的主线修订、提交、重新验收，再用一个未占用的新版本号交付。已经公开的旧标签不移动、不覆盖；简介最终指向实际验证通过的那一版。

## 当前边界与许可

没有账号隔离、云部署、自动同步、支付、备份恢复或多人编辑冲突处理。网络保存失败时保留输入、提示结果未确认，不自动重复提交；恢复后先刷新核对。删除数据库或磁盘故障仍可能丢失账目，不把教学账本当重要数据的唯一副本。

服务实现为 `app.py`，页面为 `index.html`，原始制作提示词为 `PROMPTS.txt`。GitHub Release 提供可以下载运行的源码，发布源码不等于部署在线服务。

本项目继续使用已有 `LICENSE` 中的 **MIT License，Copyright (c) 2026 Xiamo**；本次交付修订不改许可文件。
