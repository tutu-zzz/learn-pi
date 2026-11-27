# V1.1 — CLI Packaging

这一章的成果是一个可以在仓库外启动的 `micro-pi` 命令。从 V1.0 的 Agent 核心出发，依次完成命令入口、首次配置、资源打包和安装验收。[V1.0 核心教程](../README.md#v10--micro-pi-core已验收)

## 先体验成品

在 Python 3.12 的虚拟环境或你的 `learn-pi` Conda 环境中，下载并安装 Release 页面里的 wheel。[GitHub Release v1.1.0](https://github.com/tutu-zzz/learn-pi/releases/tag/v1.1.0)

```powershell
python -m pip install .\learn_pi-1.1.0-py3-none-any.whl
micro-pi --version
```

进入一个练习目录，运行 `micro-pi`。如果是第一次启动，输入模型服务的 API 根地址、模型名称和 API Key。服务须兼容 OpenAI Chat Completions 并支持 Tool Calling。API Key 输入时隐藏，验证连接成功后会进入真实对话。

```text
> 请使用 word_count 统计 one two three four 的词数。
调用工具 Tool Call: word_count, 参数: {'text': 'one two three four'}
工具执行结果 Tool Result:
Word count: 4
Answer: 这段英文有 4 个词。
```

模型措辞可能不同。看到工具调用与 `Word count: 4` 后，输入 `/exit` 退出。`micro-pi --help` 可查看启动选项，`python -m micro_pi` 提供相同入口。

## 1. 把启动脚本变成命令

把 V1.0 需要的核心模块复制到本章 `src/micro_pi/`，将模块之间的导入改为包内相对导入。把配置、恢复和输入循环放进 `cli.py` 可调用的函数，让 `import micro_pi` 不会启动对话或请求模型。

`pyproject.toml` 里的 `[project.scripts]` 指定命令名与入口函数。用 pip 安装包后，终端的 `micro-pi` 会调用 `micro_pi.cli.main()`。`__main__.py` 也调用同一函数，因此两个入口的行为一致。

```toml
[project.scripts]
micro-pi = "micro_pi.cli:main"
```

## 2. 完成首次配置

在交互终端中，缺少配置时自动启动向导。`micro-pi init` 可主动重新配置。向导先发送一条只包含 `Reply with OK.` 的消息，收到可用响应后才写入配置。配置保存在用户目录 `~/.micro-pi/config.json`，其中包含 API Key，请将它作为凭据文件保管。

也可以在当前进程环境中同时设置 `MICRO_PI_BASE_URL`、`MICRO_PI_MODEL` 和 `MICRO_PI_API_KEY`，三项作为一组优先使用。已设置其中一部分时会提示补齐。CLI 不从任意工作目录自动加载 `.env`。使用 HTTP 的模型地址限于本机服务。

## 3. 分清包资源和工作区

- `word_count` 作为 Python 扩展随包安装，启动时进入同一个 `ToolRegistry`。
- `code-review` 的 `SKILL.md` 是包数据，通过 `importlib.resources` 加载，由工具路径 `@skill/code-review` 读取。
- 启动目录就是文件工具的工作区。首次运行任务时，程序在该目录的 `.micro-pi/` 下保存 Parent、Explorer 和 Comparator 会话以及 `run.json`。换目录会使用另一份历史，模型配置可继续使用。
- `.micro-pi/` 和 `.env` 不开放给文件工具。Sandbox 仍是 V1.0 的工具名白名单，默认拒绝 `bash`。仅运行你信任的工作区，已有的 Checkpoint 会在启动时恢复。

## 4. 安装亲手写的版本

在仓库根目录执行以下命令。安装完成后，换到空白练习目录，再用 `micro-pi --help` 检查命令，用真实模型重跑开头的词数统计。

```powershell
cd learning-versions/16_v1.1_cli
python -m pip install .
```

准备发布时，在本章目录构建 wheel。将 `dist/` 内的 wheel 安装到干净的 Python 3.12 环境，再运行 `tests/` 中的测试。Release 附带的 `SHA256SUMS.txt` 可用于对照 `Get-FileHash` 或 `sha256sum` 的结果。

```powershell
python -m pip install build
python -m build --wheel
```

最后可以在工作区用 `read` 读取一个样例文件，要求 Agent 读取内置 Skill 或委托 Explorer，再用 `/exit` 和重启观察历史恢复。V1.0 的 Session 目录与 V1.1 的工作区状态各自独立。
