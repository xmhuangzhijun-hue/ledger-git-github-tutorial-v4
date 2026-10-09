# 随手账 · 第二集：后端与数据库

同一台 Windows 电脑上的独立浏览器，通过同一后端读写 SQLite 账本。教学案例，无账号隔离；仅绑定本机，不应直接作为公开记账服务。示例金额不是真实个人消费。

## Windows 运行

安装官方 Python 3.11 或以上并能运行 `py`，解压项目，在文件夹空白处打开终端：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

首次准备依赖需要网络；之后启动不需要模型或AI账号。不需要激活虚拟环境，也不需要改变 PowerShell 执行策略。

浏览器打开 **http://127.0.0.1:8000**。另一个浏览器也输入相同地址。需要手动刷新，不是实时推送。`127.0.0.1` 指当前电脑；把该地址发给朋友不能访问你的服务。

按 Ctrl+C 停止。重新运行上面的启动命令，使用同一数据库。端口冲突会明确报错，不会自动换端口或终止其它程序；可显式使用：

```powershell
.\.venv\Scripts\python.exe app.py --port 8001
```

此时两个浏览器和接口验收都改用 http://127.0.0.1:8001。

## 数据位置和边界

- 默认 `data/ledger.sqlite3`，相对于 `app.py`，不会随终端工作目录变化。首次启动创建空表。
- 旧版 `legacy.html` 的 localStorage 没有迁移；不要清理原来的浏览器数据。旧版仍保留供比较。
- 支持新增、修改、查看、删除正常支出。金额按严格正整数分存储；明细、记录数和合计使用所选月份。
- 没有账号隔离、云部署、自动同步、支付、备份恢复或多人并发编辑冲突处理。一次数据库事务不等于完整的多用户产品。
- 网络请求失败时，页面保留输入并提示结果未确认，不自动重新提交。恢复服务后先刷新核对，避免重复记账。
- 删除数据库、磁盘损坏仍会丢失数据，不把教学数据库当重要账目的唯一副本。

## 亲手验收

使用空的教学数据库：A记32元午饭，B刷新看到32；B修改原记录为23，A刷新后1笔/合计23；停服后在已打开页面保存8元饮料，页面提示未确认，输入保留；重启后还是1笔23元。

用Python自带sqlite3只读查询，不用安装sqlite3 CLI：

```powershell
.\.venv\Scripts\python.exe inspect_db.py
.\.venv\Scripts\python.exe check_api.py
```

`inspect_db.py` 不写数据库，文件不存在会报错，不创建空库掩盖路径问题。`check_api.py` 向运行中的后端发送应被拒绝的输入，核对返回码和记录是否不变，不插入正常示例数据。

```powershell
.\.venv\Scripts\python.exe check_api.py --url http://127.0.0.1:8001
```

服务实现：`app.py`；界面：`index.html`；完整制作提示词：`PROMPTS.txt`。MIT许可。

个人博客：https://huangzhijun.online/
系列仓库：https://github.com/xmhuangzhijun-hue/ledger-mvp
本地第二集交付包独立提供；公开仓库未更新时请以本包为准。
