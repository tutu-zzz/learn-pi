# micro-pi 版本学习指南

[← 返回项目首页](../README.md)

这里保存 `micro-pi` 从一次 LLM 调用成长为终端 Agent 的完整学习路径。每个版本只增加一个主要能力；点击标题即可展开对应说明。

## 如何使用

1. 从 V0.1 开始，先运行代码再阅读说明。
2. 理解上一版遇到的问题，再观察这一版新增的机制。
3. 重点阅读代码中的 `[V0.x 新增]` 和 `[V0.x 修改]` 注释。
4. 完成“建议观察”中的实验后，再进入下一版。

> V0.1–V0.11 已完成并通过测试。所有命令均从项目根目录运行，输入 `/exit` 可以结束对话。

## 已完成版本

<details>
<summary><strong>📌 V0.1 — First LLM Call：一次模型请求发生了什么？</strong></summary>

**本版目标**

打通最小链路：读取终端输入，调用一次 LLM，再把回答输出到终端。

~~~text
加载配置
  → 构造 Messages
  → 发送 HTTP 请求
  → 解析模型回答
  → 输出到终端
~~~

**核心内容**

| 概念 | 作用 |
| --- | --- |
| `.env` | 保存 Base URL、Model 和 API Key |
| `messages` | 描述 system 指令和本次 user 输入 |
| `requests.post` | 向 `/chat/completions` 发送 JSON 请求 |
| `choices[0].message` | 从响应中取得模型回答 |

**运行**

~~~bash
python learning-versions/01_v0.1_first_llm_call/main.py
~~~

**建议观察**

- 用户输入如何变成请求体中的 `messages`。
- HTTP 请求头和请求体分别承担什么职责。
- API Key 是否始终没有被打印到终端。
- 当前为什么只能完成一问一答。

**代码：** [main.py](01_v0.1_first_llm_call/main.py)

</details>

<details>
<summary><strong>📌 V0.2 — Conversation：模型为什么能记住前文？</strong></summary>

**本版目标**

在同一次程序运行中保存消息历史，让模型能够完成多轮对话。

~~~text
创建 messages
  → 追加 user 消息
  → 发送完整历史
  → 追加 assistant 消息
  → 等待下一轮输入
~~~

**核心内容**

| 概念 | 作用 |
| --- | --- |
| 对话外层循环 | 持续接收用户输入 |
| `messages` | 保存本次运行中的完整消息历史 |
| user / assistant | 区分消息的发送者 |
| `/exit` | 主动结束当前程序 |

**运行**

~~~bash
python learning-versions/02_v0.2_conversation/main.py
~~~

**建议观察**

- 第一轮告诉模型一个名字，第二轮再询问名字。
- `messages` 为什么必须创建在循环外。
- 模型并非自己长期记忆，而是每轮都重新收到历史消息。
- 程序退出后历史会消失，此时还没有 Session。

**代码：** [main.py](02_v0.2_conversation/main.py)

</details>

<details>
<summary><strong>📌 V0.3 — Tool Calling：模型如何提出工具请求？</strong></summary>

**本版目标**

完成一次完整的工具调用，让模型根据真实文件内容回答问题。

~~~text
定义 Tool Schema
  → 模型生成 Tool Call
  → Runtime 解析工具与参数
  → Python 执行 read_file
  → 返回 Tool Result
  → 模型生成 Final Answer
~~~

**核心内容**

| 概念 | 作用 |
| --- | --- |
| Tool Schema | 告诉模型工具名称、用途和参数格式 |
| Tool Call | 模型生成的结构化工具请求 |
| Tool Runtime | 真正调用 Python 函数的程序 |
| Tool Result | 工具执行后返回给模型的真实结果 |
| `tool_call_id` | 将结果与原始 Tool Call 对应起来 |

**运行**

~~~bash
python learning-versions/03_v0.3_tool_calling/main.py
~~~

**建议观察**

- 模型只提出调用请求，并没有亲自读取文件。
- `function.arguments` 为什么需要从 JSON 字符串解析。
- Tool Result 为什么必须再次加入 `messages`。
- V0.3 为什么只能处理预设的一次工具调用。

**代码：** [main.py](03_v0.3_tool_calling/main.py)

</details>

<details>
<summary><strong>📌 V0.4 — Agent Loop：Agent 为什么需要循环？</strong></summary>

**本版目标**

把固定次数的模型调用改成循环，让任务可以经历任意次数的“模型决策 → 工具执行”。

~~~text
调用模型
  → 有 Tool Call：执行工具并回传结果
  → 再次调用模型
  → 没有 Tool Call：输出最终回答并结束
~~~

**核心内容**

| 循环 | 职责 |
| --- | --- |
| 外层对话循环 | 持续接收新的用户任务 |
| 内层 Agent Loop | 持续处理当前任务，直到模型给出最终回答 |
| 结束条件 | assistant message 中不存在 `tool_calls` |

**运行**

~~~bash
python learning-versions/04_v0.4_agent_loop/main.py
~~~

**建议观察**

- 模型调用次数为什么不再固定。
- 有 Tool Call 和没有 Tool Call 时分别走哪条分支。
- 工具结果如何成为下一轮模型决策的上下文。
- Agent 与普通单轮 LLM 调用的核心差异。

**代码：** [main.py](04_v0.4_agent_loop/main.py)

</details>

<details>
<summary><strong>📌 V0.5 — Tool Registry：工具多了以后如何管理？</strong></summary>

**本版目标**

使用 Tool Registry 集中保存工具说明和执行函数，让 Runtime 可以按名称查找工具。

~~~text
定义工具函数
  → 注册 description / parameters / execute
  → 自动生成 Tool Schema
  → 按工具名查找
  → 执行对应函数
~~~

**核心内容**

| Registry 字段 | 使用者 |
| --- | --- |
| `description` | 模型，用于理解工具用途 |
| `parameters` | 模型，用于生成正确参数 |
| `execute` | Runtime，用于调用真正的 Python 函数 |

**运行**

~~~bash
python learning-versions/05_v0.5_tool_registry/main.py
~~~

**建议观察**

- Tool Schema 如何从 Registry 自动生成。
- Runtime 如何通过工具名找到 `execute`。
- 新增工具时为什么不再需要扩展一长串 `if/elif`。
- “给模型看的说明”和“给 Runtime 用的函数”如何放在同一注册项中。

**代码：** [main.py](05_v0.5_tool_registry/main.py)

</details>

<details>
<summary><strong>📌 V0.6 — Mini Coding Agent：能做什么？</strong></summary>

**本版目标**

加入四个 Coding Tools，让 Agent 能够读取、创建、编辑文件并执行项目命令。

~~~text
接收编码任务
  → 模型选择 read / write / edit / bash
  → Tool Registry 分发
  → Runtime 执行工具
  → 返回 Tool Result
  → Agent Loop 继续
~~~

**核心内容**

| Tool | 能力 |
| --- | --- |
| `read` | 读取工作目录中的文本文件 |
| `write` | 创建或覆盖文件 |
| `edit` | 将指定文本替换一次 |
| `bash` | 在工作目录中执行 Shell 命令 |
| `resolve_path` | 阻止文件工具访问工作目录之外的路径 |

**运行**

~~~bash
python learning-versions/06_v0.6_mini_coding_agent/main.py
~~~

可以尝试：

~~~text
创建 hello.py，让它输出 Hello, micro-pi!，然后运行它。
~~~

**建议观察**

- 一个编码任务如何拆成多个 Tool Call。
- 工具异常为什么也要作为 Tool Result 返回模型。
- `read / write / edit` 的路径检查能够限制什么。
- `bash` 仍直接使用系统 Shell，为什么还不能称为 Sandbox。

> **安全提示：** 请只在测试目录或可恢复环境中运行本版本，不要使用包含敏感数据的目录或高权限账户。

**代码：** [main.py](06_v0.6_mini_coding_agent/main.py)

</details>

<details>
<summary><strong>📌 V0.7 — Session：程序重启后如何继续对话？</strong></summary>

**本版目标**

把每条消息持久化为 JSONL，并在程序启动时恢复历史，实现跨进程继续对话。

~~~text
启动程序
  → 加载 Session
  → 恢复 messages
  → 保存 user / assistant / tool 消息
  → 退出程序
  → 再次启动并恢复历史
~~~

**核心内容**

| 概念 | 作用 |
| --- | --- |
| JSONL | 每行保存一个独立的 JSON 消息对象 |
| `load_session` | 启动时逐行解析历史消息 |
| `add_message` | 同时写入内存列表和 Session 文件 |
| `sessions/` | 保存运行数据，已被 Git 忽略 |

**运行**

~~~bash
python learning-versions/07_v0.7_session/main.py
~~~

**建议观察**

- 第一次运行后 `sessions/*.jsonl` 中保存了哪些角色。
- 退出并重新启动后，模型能否回答之前提供的信息。
- Tool Call 和 Tool Result 为什么也要进入 Session。
- Session、当前 Context 和长期 Memory 为什么不是同一个概念。

**代码：** [main.py](07_v0.7_session/main.py)

</details>

<details>
<summary><strong>📌 V0.8 — Context Compaction：如何压缩上下文？</strong></summary>

**本版目标**

将完整 Session 与模型 Context 分离，把较早的消息总结为 Summary，同时保留最近对话。

~~~text
完整 Session
  → 复制为 Context
  → 超过消息限制
  → 旧消息生成 Summary
  → 保留 Summary + 最近两轮
  → 发送精简 Context
~~~

**核心内容**

| 概念 | 作用 |
| --- | --- |
| `messages` | 保留完整、原始的 Session |
| `context_messages` | 当前实际发送给模型的消息 |
| `MAX_CONTEXT_MESSAGES = 8` | 教学版的压缩触发限制 |
| `RECENT_TURNS = 2` | 压缩后原样保留的最近用户回合 |
| Summary | 保存旧对话中的事实、决策和未完成任务 |

**运行**

~~~bash
python learning-versions/08_v0.8_context_compaction/main.py
~~~

**建议观察**

- 前四轮为什么不会触发压缩，第五轮为什么会触发。
- Summary 为什么只进入 Context，不写回完整 Session。
- 压缩后模型能否继续记住名字、喜好和学习目标。
- 当前实现按消息数量判断，而不是按精确 Token 数量判断。
- provider-specific `reasoning` 为什么不写入 Session。

触发成功时终端会显示：

~~~text
Context compacted: 6 messages → 1 summary
~~~

**代码：** [main.py](08_v0.8_context_compaction/main.py)

</details>

<details>
<summary><strong>📌 V0.9 — Skill：工具和技能有什么区别？</strong></summary>

**本版目标**

发现 Skill 的简短元数据，并在任务匹配时按需读取完整 `SKILL.md`，再按照其中的方法完成任务。

~~~text
定位 SKILL.md
  → 读取 name 和 description
  → 暴露可用 Skill
  → 模型识别匹配任务
  → read 完整指令
  → 按 Skill 完成任务
~~~

**核心内容**

| 概念 | 作用 |
| --- | --- |
| Skill 元数据 | 用很少的 Context 告诉模型有哪些技能 |
| `SKILL.md` | 保存完整工作方法和输出要求 |
| 按需加载 | 只有任务匹配时才读取完整说明 |
| Tool | 执行动作 |
| Skill | 指导 Agent 如何组合动作完成任务 |

**运行**

~~~bash
python learning-versions/09_v0.9_skill/main.py
~~~

**建议观察**

- 启动时进入 system message 的是否只有 Skill 元数据。
- 模型何时决定读取完整 `SKILL.md`。
- `code-review` Skill 如何约束分析步骤和输出格式。
- Skill 如何复用现有 `read` Tool，而不是新增执行能力。

**代码：** [main.py](09_v0.9_skill/main.py) · [SKILL.md](09_v0.9_skill/skills/code-review/SKILL.md)

</details>

<details>
<summary><strong>📌 V0.10 — Extension：如何在核心之外扩展能力？</strong></summary>

**本版目标**

从独立 Python 模块动态加载 Extension，并通过最小 `ExtensionAPI` 注册新工具。

~~~text
扫描 extensions 目录
  → 动态加载 Python 模块
  → 调用 setup(pi)
  → register_tool
  → 生成完整 Tool Schema
  → 模型调用扩展工具
~~~

**核心内容**

| 概念 | 作用 |
| --- | --- |
| `ExtensionAPI` | 向外部模块暴露最小注册接口 |
| `setup(pi)` | Extension 的统一入口 |
| `register_tool` | 将外部工具加入 Tool Registry |
| `word_count` | 示例 Extension Tool |
| Small Core | 核心只负责加载与注册，不包含所有工具实现 |

**运行**

~~~bash
python learning-versions/10_v0.10_extension/main.py
~~~

**建议观察**

- 程序启动时是否输出 `Extension loaded: word_count`。
- `word_count.py` 如何在 Agent Core 之外定义工具。
- Extension 注册发生在生成 Tool Schema 之前的原因。
- 新增扩展工具时，核心 Agent Loop 为什么不需要修改。

**代码：** [main.py](10_v0.10_extension/main.py) · [word_count.py](10_v0.10_extension/extensions/word_count.py)

</details>

<details>
<summary><strong>📌 V0.11 — Event：Runtime 与终端展示如何解耦？</strong></summary>

**本版目标**

使用结构化 Event 替代 Agent Loop 中面向终端的直接输出，让独立 Renderer 决定如何展示运行过程。

~~~text
Agent Runtime
  → emit Event
  → Event Observer
  → CLI Renderer
  → Terminal
~~~

**核心内容**

| Event / 组件 | 作用 |
| --- | --- |
| `tool_start` | 通知观察者即将执行哪个工具 |
| `tool_end` | 携带工具执行结果 |
| `agent_end` | 携带本轮最终回答 |
| Event Observer | 接收 Runtime 发出的结构化事件 |
| `renderer.py` | 将事件转换为终端输出 |

**运行**

~~~bash
python learning-versions/11_v0.11_event_and_streaming/main.py
~~~

**建议观察**

- Agent Loop 是否还直接负责打印工具和最终回答。
- Runtime 发出的 Event 数据包含哪些字段。
- 更换 Renderer 为什么不需要修改 Agent Core。
- Streaming 为什么不影响 Agent 核心任务结果。
- 未来如何通过 `model_delta` Event 接入流式展示。

> 当前核心版本继续使用非流式模型调用，Streaming 作为可选增强能力保留。

**代码：** [main.py](11_v0.11_event_and_streaming/main.py) · [renderer.py](11_v0.11_event_and_streaming/renderer.py)

</details>

## 后续路线

以下版本尚未实现，只保留学习目标，不提前编写实现细节：

| 版本 | 主题 | 要解决的问题 | 状态 |
| --- | --- | --- | :---: |
| V0.12 | Sandbox | 如何限制工具执行的风险？ | 🗓️ |
| V0.13 | SubAgent | 如何把任务拆给多个 Agent？ | 🗓️ |
| V0.14 | Durable Run | Agent 中断后如何恢复执行？ | 🗓️ |
| V1.0 | micro-pi Core | 如何形成完整、可解释的 Agent Core？ | 🗓️ |

---

[返回项目首页](../README.md) · [查看完整 PRD](../docs/learn-pi_-_micro-pi_PRD.md) · [查看验收进度](../docs/进度.md)
