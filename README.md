![learn-pi：Learn Agent by Building One](docs/assets/learn-pi-cover.png)

<div align="center">

# learn-pi

**Learn Agent by building a micro Pi.**

亲手写一个 Agent，真正学会 Agent。

`Minimal · Transparent · Educational · Terminal-native`

<p><strong>Agent 不是魔法。</strong><br>它只是由一组可以理解、可以实现、可以观察的机制组合而成。</p>

</div>

---

## 📖 这是什么项目？

`learn-pi` 是一个面向 Agent 初学者的渐进式学习项目。

它不从大型框架开始，也不把 Agent 包装成黑盒，而是从一次最普通的 LLM 请求出发，每个版本只增加一个关键能力，最终亲手实现一个极简、透明、运行在终端中的 Coding Agent：`micro-pi`。

~~~text
一次 LLM 调用
    ↓
多轮对话
    ↓
Tool Calling
    ↓
Agent Loop
    ↓
Tool Registry
    ↓
Coding Agent
    ↓
Session / Context / Skill / Extension / Event ...
~~~

> 这个项目的目标不是“再造一个完整的 Pi”，而是借鉴 Pi 的极简思想，把 Agent 的核心机制一层一层拆开。

## ✨ 为什么要做 learn-pi？

使用 Agent 框架很容易，真正解释清楚它为什么能工作却不容易：

- 模型为什么能“记住”上一句话？
- Tool Call 是模型执行的吗？
- Tool Result 为什么还要发回给模型？
- Agent 和普通 ChatBot 的区别是什么？
- 为什么一段 `while` 循环会成为 Agent 的核心？
- Session、Context、Memory 分别是什么？

`learn-pi` 希望通过“少量代码 → 立即运行 → 观察现象 → 理解机制”的方式，让这些问题不再神秘。

| 原则 | 含义 |
| --- | --- |
| **Minimal** | 每个版本只解决一个主要问题，不提前堆功能 |
| **Transparent** | 请求、消息、工具调用和运行过程都能直接看到 |
| **Educational** | 代码优先服务于理解，再考虑抽象与工程化 |
| **Terminal-native** | 聚焦 Agent Runtime，不让界面复杂度干扰学习 |

## 🚦 当前进度

当前已经完成并验收到 **V0.11 — Event**，下一阶段将进入 **V0.12 — Sandbox**。Streaming 不影响 Agent 核心能力，暂时作为可选增强保留。

| 版本 | 主题 | 状态 |
| --- | --- | :---: |
| V0.1 | First LLM Call | ✅ |
| V0.2 | Conversation | ✅ |
| V0.3 | Tool Calling | ✅ |
| V0.4 | Agent Loop | ✅ |
| V0.5 | Tool Registry | ✅ |
| V0.6 | Mini Coding Agent | ✅ |
| V0.7 | Session | ✅ |
| V0.8 | Context Compaction | ✅ |
| V0.9 | Skill | ✅ |
| V0.10 | Extension | ✅ |
| V0.11 | Event（Streaming 可选） | ✅ |
| V0.12 | Sandbox | 🗓️ |
| V0.13 | SubAgent | 🗓️ |
| V0.14 | Durable Run | 🗓️ |
| V1.0 | micro-pi Core | 🗓️ |

> `✅ 已完成` · `🗓️ 计划中`

### 📚 版本学习入口

每个已完成版本的目标、流程、运行方法和观察重点已集中整理：

> **[查看 V0.1–V0.11 版本详细说明 →](learning-versions/README.md)**

## 🚀 快速开始

### 1. 准备环境

- Python 3.12（项目当前开发环境）
- 一个提供 `/chat/completions` 接口的 OpenAI-compatible 模型服务
- 从 V0.3 开始，模型还需要支持 Tool Calling

克隆项目：

~~~bash
git clone https://github.com/tutu-zzz/learn-pi.git
cd learn-pi
~~~

Windows PowerShell：

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
~~~

macOS / Linux：

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
~~~

### 2. 配置模型

打开项目根目录中的 `.env`：

~~~dotenv
MICRO_PI_BASE_URL=https://your-provider.example/v1
MICRO_PI_MODEL=your-model-name
MICRO_PI_API_KEY=your-api-key
~~~

| 配置项 | 作用 |
| --- | --- |
| `MICRO_PI_BASE_URL` | 模型服务的 API 根地址，不包含 `/chat/completions` |
| `MICRO_PI_MODEL` | 服务商提供的模型名称 |
| `MICRO_PI_API_KEY` | API 访问密钥 |

> 🔐 `.env` 已被 Git 忽略。请勿把真实 API Key 写入源码、截图或提交记录。

### 3. 运行项目

第一次学习建议从 V0.1 开始：

~~~bash
python learning-versions/01_v0.1_first_llm_call/main.py
~~~

输入一条消息：

~~~text
> 你好，请用一句话介绍 Agent。
Answer: ...
~~~

如果希望体验当前最新的完整版本：

~~~bash
python learning-versions/11_v0.11_event_and_streaming/main.py
~~~

对话中输入 `/exit` 可以退出程序。其余版本的运行方式与学习重点请查看[版本学习指南](learning-versions/README.md)。

## 🧠 Agent 到底是怎么工作的？

从 V0.4 开始，`micro-pi` 已经具备最小 Agent Loop：

~~~mermaid
flowchart LR
    U["用户输入"] --> R["Agent Runtime"]
    R --> L["LLM"]
    L -->|"Final Answer"| O["输出回答"]
    L -->|"Tool Call"| T["Tool Registry"]
    T --> E["Python 执行工具"]
    E -->|"Tool Result"| R
~~~

最关键的认知是：

1. **模型不会亲自执行工具。** 模型只生成结构化的 Tool Call。
2. **Python Runtime 才是真正的执行者。** 它解析参数、调用函数并得到结果。
3. **工具结果需要返回给模型。** 模型拿到真实结果后，才能决定继续调用工具还是给出最终回答。
4. **Agent Loop 负责重复这个过程。** 直到模型不再请求工具，本轮任务才结束。

最小逻辑可以理解为：

~~~python
while True:
    assistant_message = call_model(messages)

    if not assistant_message.get("tool_calls"):
        print(assistant_message["content"])
        break

    for tool_call in assistant_message["tool_calls"]:
        tool_result = execute_tool(tool_call)
        messages.append(tool_result)
~~~

这段循环并不等于完整的生产级 Agent，但它已经揭示了 Agent 最核心的运行机制。

## 🗺️ 推荐学习方式

不要直接阅读最终版本。建议每一版都按下面的顺序学习：

1. **先运行上一版**：确认它已经能做什么。
2. **再提出新问题**：理解为什么需要增加下一个能力。
3. **只看本版新增内容**：代码中的 `[V0.x 新增]` 和 `[V0.x 修改]` 会标出变化。
4. **亲手输入测试任务**：观察 Message、Tool Call、Tool Result 和 Event。
5. **尝试删掉关键代码**：根据运行变化解释它的职责。
6. **最后进入下一版**：带着问题理解新抽象，而不是背结论。

每学完一个版本，尝试回答：

- 这一版解决了上一版的什么问题？
- 新增能力由模型、Runtime 还是工具负责？
- 如果删掉这部分代码，用户能观察到什么变化？

具体学习路径请从[可折叠版本说明](learning-versions/README.md)中按顺序展开。

## 📁 项目结构

~~~text
learn-pi/
├── docs/
│   ├── assets/
│   │   └── learn-pi-cover.png
│   ├── learn-pi_-_micro-pi_PRD.md
│   └── 进度.md
├── learning-versions/
│   ├── 01_v0.1_first_llm_call/
│   ├── 02_v0.2_conversation/
│   ├── 03_v0.3_tool_calling/
│   ├── 04_v0.4_agent_loop/
│   ├── 05_v0.5_tool_registry/
│   ├── 06_v0.6_mini_coding_agent/
│   ├── 07_v0.7_session/
│   ├── 08_v0.8_context_compaction/
│   ├── 09_v0.9_skill/
│   │   └── skills/code-review/SKILL.md
│   ├── 10_v0.10_extension/
│   │   ├── extensions/word_count.py
│   │   └── skills/code-review/SKILL.md
│   ├── 11_v0.11_event_and_streaming/
│   │   ├── main.py
│   │   ├── renderer.py
│   │   ├── extensions/word_count.py
│   │   └── skills/code-review/SKILL.md
│   ├── 12_v0.12_sandbox/             # 计划中
│   ├── 13_v0.13_subagent/            # 计划中
│   ├── 14_v0.14_durable_run/         # 计划中
│   ├── 15_v1.0_micro_pi_core/        # 计划中
│   └── README.md                     # 可折叠版本学习指南
├── sessions/                         # 运行时生成，已被 Git 忽略
├── src/
│   └── micro_pi/
│       └── main.py                   # 主学习工作区
├── .env.example
├── requirements.txt
└── README.md
~~~

`learning-versions/` 保存每个阶段的独立代码快照。旧版本不会继续叠加修改，因此可以清楚地比较 Agent 是怎样一步一步成长的。

## 📚 延伸阅读

- [版本学习指南：按需展开每个版本](learning-versions/README.md)
- [完整 PRD：项目定位、设计原则与长期路线](docs/learn-pi_-_micro-pi_PRD.md)
- [项目进度：各版本验收记录](docs/进度.md)

## 🤝 参与项目

欢迎通过 Issue 或 Pull Request 交流：

- 某个概念是否还能讲得更直白
- 某一步是否对初学者跳跃过大
- 示例、注释或错误提示是否可以改进
- 新版本是否仍然遵循“一个阶段只引入一个主要概念”

如果你正在跟学，也欢迎记录自己的问题。一个“看起来很基础”的问题，往往正是教程最值得补充的地方。

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。
