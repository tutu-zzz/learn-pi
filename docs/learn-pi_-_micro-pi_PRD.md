# learn-pi — PRD

> 版本：V0.1  
> 项目阶段：学习验证期  
> 项目类型：Agent 学习 / 极简 Agent 实现 / 教学型开源项目  
> 项目名称：`learn-pi`  
> 核心程序：`micro-pi`  
> 主要语言：Python  
> 产品形态：Terminal-native CLI / 极简终端 Agent  
> 参考方向：Pi Agent  
> 核心原则：Minimal · Transparent · Educational · Terminal-native

---

# 1. 项目名称

## 1.1 项目名称

```text
learn-pi
```

`learn-pi` 是整个学习项目、GitHub 仓库以及未来教程体系的名称。

它表达的是：

> 通过亲手实现一个极简 Pi-style Agent，真正学习 Agent。

---

## 1.2 核心程序名称

```text
micro-pi
```

`micro-pi` 是 `learn-pi` 项目中最终一步一步实现出来的极简 Agent。

两者关系：

```text
learn-pi
│
│  学习项目 / 教程体系
│
└── micro-pi
     │
     └── 亲手实现的极简 Agent
```

可以理解为：

```text
learn-pi
= 如何学习

micro-pi
= 最终做出来什么
```

---

# 2. 一句话定位

> **learn-pi 是一个以 Pi 的极简思想为参考的 Agent 学习项目：从一次 LLM 调用开始，用尽可能少的 Python 代码，一步一步实现一个透明、极简、运行在终端中的 micro-pi，并最终沉淀成一套真正适合 Agent 小白的渐进式教程。**

---

# 3. 项目 Slogan

英文：

> **Learn Agent by building a micro Pi.**

中文：

> **亲手写一个 Agent，真正学会 Agent。**

---

# 4. 项目背景

当前 Agent 生态已经存在大量成熟框架和 Coding Agent。

开发者可以非常快速地获得：

```text
LLM
Tool
Memory
MCP
RAG
Workflow
Multi-Agent
Sandbox
```

等能力。

但对于刚开始学习 Agent 的开发者，一个非常常见的问题是：

> 项目跑起来了，但自己不知道为什么能跑起来。

尤其在 AI Coding 越来越普遍以后，开发者很容易：

```text
提出需求
  ↓
AI 生成代码
  ↓
运行成功
```

但是对代码背后的机制没有建立完整认知。

最终可能无法清楚回答：

- 一次 LLM 调用到底发生了什么？
- Provider 和 Model 是什么？
- Message 是什么？
- Context 是什么？
- 模型为什么能够调用 Tool？
- Tool 到底是谁执行的？
- Tool Result 为什么还要再次发送给模型？
- Agent 和普通 ChatBot 有什么区别？
- Agent Loop 为什么通常需要循环？
- Agent Loop 什么时候结束？
- Tool 多了以后如何管理？
- Session 和 Context 有什么区别？
- Memory 又是什么？
- Context 超长之后怎么办？
- Skill 和 Tool 有什么区别？
- Extension 为什么存在？
- Agent 为什么需要 Sandbox？
- 一个 Agent 不够时怎么办？
- Agent 执行到一半崩溃怎么办？

Agent 因此很容易成为一个“黑盒”。

`learn-pi` 的目标就是：

> 把这个黑盒一点一点拆开。

---

# 5. 为什么选择 Pi

本项目选择 Pi 作为长期参考目标，最主要的原因不是功能数量，而是：

> 极简。

本项目希望学习的不是：

```text
如何快速堆出很多 Agent 功能
```

而是：

```text
Agent 最核心的部分到底是什么？
```

因此不会一开始完整复现 Pi。

目标也不是：

```text
Pi Clone
```

而是：

```text
Pi-inspired Minimal Agent
```

即：

> 提取 Pi 最核心的 Agent 思想，通过自己的最小实现去理解这些机制。

---

# 6. learn-pi 与 Pi 的关系

整个学习过程遵循：

```text
自己先实现
      ↓
自己真正理解
      ↓
再阅读真实 Pi
      ↓
找到 Pi 中对应设计
      ↓
比较差异
      ↓
理解为什么成熟项目更加复杂
```

而不是：

```text
打开 Pi 源码
      ↓
照着复制
      ↓
得到另一个 Pi
```

因此，`learn-pi` 的核心问题始终是：

> **为什么需要这个机制？**

而不是：

> Pi 的这段代码怎么抄过来？

---

# 7. 核心设计哲学

项目遵循四个核心关键词：

```text
Minimal

Transparent

Educational

Terminal-native
```

---

# 8. Minimal — 极简

极简不仅是界面风格，也是整个项目的工程原则。

原则：

> 如果一个抽象当前没有必要，就先不要引入。

例如项目最开始可能只有：

```text
learn-pi/
├── src/
│   └── main.py
│
├── README.md
└── PRD.md
```

而不是第一天就创建：

```text
agent/
runtime/
provider/
context/
session/
memory/
events/
skills/
extensions/
sandbox/
```

这些目录应该随着真实需求自然产生。

每新增一个模块，都必须能够回答：

> 为什么现在需要它？

---

# 9. Transparent — 透明

普通 Agent 产品通常希望隐藏内部复杂过程，只告诉用户最终结果。

`micro-pi` 刚好相反。

因为它首先是一个学习型 Agent。

因此：

> **不要隐藏 Agent Loop，要把 Agent 的运行过程展示出来。**

例如：

```text
> 检查 calculator.py 并运行测试

● read
  calculator.py

● read
  test_calculator.py

● bash
  pytest

✗ 1 test failed

● edit
  calculator.py

● bash
  pytest

✓ 5 tests passed

已经完成修改。
```

学习者应该能够直接看到：

```text
Model
 ↓
Tool
 ↓
Model
 ↓
Tool
 ↓
Model
 ↓
Final Answer
```

并最终把终端表现与代码中的：

```python
while True:
    ...
```

联系起来。

---

# 10. Educational — 教学优先

`micro-pi` 首先服务于：

```text
理解
```

而不是：

```text
生产能力
```

因此教学代码的优先级是：

```text
可理解
>
因果关系清晰
>
可运行
>
抽象漂亮
>
工程完整
```

生产级代码则通常更强调：

```text
稳定性
扩展性
性能
安全
异常处理
```

两者必须明确区分。

---

# 11. Terminal-native — 终端原生

`micro-pi` 不计划从 Web UI 开始。

最终核心体验始终是：

```bash
micro-pi
```

进入 Agent。

用户不需要：

```text
启动前端
启动后端
打开浏览器
配置数据库
```

而是：

```text
Terminal
   │
   ▼
micro-pi
```

直接进入。

---

# 12. micro-pi 不是什么

`micro-pi` 不是 Terminal Emulator。

不会自行实现类似：

- Windows Terminal
- iTerm2
- WezTerm

这样的底层终端。

实际关系是：

```text
Windows Terminal / Linux Terminal
              │
              ▼
          micro-pi
              │
              ▼
          Agent Runtime
```

因此更准确的定义是：

> **Terminal-native Agent Application**

---

# 13. 产品界面原则

最终界面保持克制。

核心只需要三个区域：

```text
┌───────────────────────────────────┐
│                                   │
│        Conversation               │
│                                   │
│        Tool Activity              │
│                                   │
├───────────────────────────────────┤
│ > Input                           │
├───────────────────────────────────┤
│ model · cwd · context             │
└───────────────────────────────────┘
```

不优先增加：

- 复杂 Sidebar
- 多个 Dashboard
- Agent 管理页面
- Kanban
- 文件管理器
- Web 面板

原则：

> 终端只是 Agent 的容器，Agent 才是主角。

---

# 14. 项目总体目标

项目分为三个长期阶段。

---

# 15. Phase 1 — Learn Agent

## 目标

首先服务于项目作者本人。

目标：

> 从 0 开始，通过少量手写代码真正理解 Agent。

第一阶段重点掌握：

```text
LLM
Message
Conversation
Context
Tool Calling
Tool Result
Agent Loop
Tool Registry
Coding Tools
Session
Compaction
Skill
Extension
Event
```

此阶段：

> 学会比做完更重要。

---

# 16. Phase 2 — Teach Agent

完成第一轮学习后，将真实学习过程整理为一套正式教程。

素材来源包括：

- 原来不理解的问题
- 理解错误的地方
- 实际踩过的坑
- 最容易理解的解释
- 最小代码
- Debug 过程
- 流程图
- Pi 源码对照

最终形成：

> 一套真正从 Agent 小白视角设计的教学内容。

---

# 17. Phase 3 — Engineer Agent

完成 Agent Core 后，再逐渐进入：

```text
Sandbox
Permission
SubAgent
Concurrency
Worker
Durable Run
Observability
Evaluation
```

最终从：

```text
学习型 Agent
```

逐渐理解：

```text
Production Agent Runtime
```

---

# 18. 核心学习方法：Problem First

教程不采用：

```text
这是 Tool Calling。

这是 Agent Loop。

这是 Session。
```

而采用：

```text
当前版本
   ↓
出现问题
   ↓
为什么解决不了？
   ↓
需要什么新机制？
   ↓
手写最小版本
   ↓
运行
   ↓
解决问题
   ↓
这个机制原来叫 XXX
```

例如：

```text
LLM 只能说话
       ↓
不能读取 README
       ↓
怎么办？
       ↓
给模型描述一个 read 工具
       ↓
模型请求 read
       ↓
Python 真正执行
       ↓
把结果返回模型
       ↓
这就是 Tool Calling
```

---

# 19. 核心学习原则

## 19.1 每一阶段只引入一个主要概念

例如：

```text
V0.1
LLM Call

V0.2
Conversation

V0.3
Tool Calling

V0.4
Agent Loop
```

避免一次出现：

```text
Tool
Memory
MCP
RAG
Multi-Agent
Sandbox
Workflow
```

---

## 19.2 代码随着问题自然增长

不提前设计“大而全架构”。

例如：

```text
main.py
```

发现模型相关代码越来越多：

```text
main.py
llm.py
```

发现 Tool 需要独立：

```text
tools/
```

发现 Tool 多了：

```text
registry.py
```

发现 Session 需要持久化：

```text
session/
```

也就是说：

> 每个目录都应该是被问题“逼出来”的。

---

# 20. 技术选型

## 20.1 编程语言

第一阶段：

```text
Python
```

原因：

- 已有 Python 基础
- 语法负担低
- 适合学习 Agent
- LLM SDK 生态成熟
- Agent Loop 表达简单
- 适合教学型项目

当前不为了贴近 Pi 强制学习 TypeScript。

---

# 21. 暂不使用大型 Agent Framework

第一阶段原则上不使用：

- LangChain
- LangGraph
- DeepAgents
- AutoGen
- CrewAI
- 其他完整 Agent Harness

优先：

```text
Python
+
模型 API / SDK
+
Python 标准库
```

目标：

> 直接看到 Agent 的每一层是怎么发生的。

---

# 22. CLI 技术原则

CLI 本身也随着项目自然演化。

最初只使用：

```python
input()
print()
```

暂不优先使用复杂 TUI Framework。

后续随着需求出现，再考虑：

```text
prompt_toolkit

Rich
```

等轻量工具。

第一阶段不优先采用复杂 Textual Dashboard。

因为：

> 项目核心是学习 Agent，而不是学习如何开发复杂 TUI。

---

# 23. CLI 演化路线

CLI 自身也是教程的一部分。

---

## V0.1

```text
micro-pi

> hello

Hello!

>
```

只需要：

```text
input
 ↓
LLM
 ↓
print
```

---

## V0.2

界面几乎不变：

```text
> 我叫瀚文

你好，瀚文。

> 我叫什么？

你叫瀚文。
```

但是底层已经增加：

```text
Conversation
```

---

## V0.3

第一次展示 Agent 内部动作：

```text
> README.md 写了什么？

● read
  README.md

README 主要介绍了……
```

---

## V0.4

展示 Agent Loop：

```text
> 检查 calculator.py

● read
  calculator.py

● bash
  pytest

✗ failed

● edit
  calculator.py

● bash
  pytest

✓ passed

修改完成。
```

---

## 后续

逐渐增加：

```text
streaming
spinner
tool status
token usage
cwd
model
context usage
```

但始终保持克制。

---

# 24. V0.1 — First LLM call

## 当前目标

让 `micro-pi` 第一次和模型说话。

流程：

```text
User
 ↓
CLI
 ↓
LLM Client
 ↓
Provider
 ↓
Model
 ↓
Response
 ↓
CLI
 ↓
User
```

---

## 核心概念

学习：

```text
Provider
Model
API
Request
Response
Message
Token
API Key
```

暂时不讲 Agent。

---

## 最小体验

```bash
micro-pi
```

进入：

```text
micro-pi

> hello

Hello! How can I help you?

>
```

---

## 验收标准

能够自己解释：

- Provider 是什么？
- Model 是什么？
- API 请求是什么？
- Python 如何向模型发送请求？
- 模型返回的 Response 是什么？
- Message 是什么？

---

# 25. V0.2 — Conversation

## 当前问题

V0.1 中每次请求都是独立的。

例如：

```text
> 我叫小明

你好，小明。

> 我叫什么？
```

如果没有重新发送之前的消息，模型并不知道答案。

---

## 引入

```python
messages = []
```

形成：

```text
user
assistant
user
assistant
```

---

## 核心概念

学习：

```text
Message History
Conversation
Context
Context Window
system
user
assistant
```

---

## 必须理解

> 最简单的“模型记忆”，本质就是把之前的 Message 再发送一次。

---

# 26. V0.3 — Tool Calling

## 当前问题

模型可以聊天。

但是不能真正：

```text
读取文件
修改文件
执行程序
```

---

## 第一个 Tool

实现：

```text
read_file
```

用户：

```text
> README.md 写了什么？
```

流程：

```text
User
 ↓
Model
 ↓
Tool Call
 ↓
Python Runtime
 ↓
read_file()
 ↓
Tool Result
 ↓
Model
 ↓
Final Answer
```

---

## 核心概念

学习：

```text
Tool
Tool Schema
Tool Name
Tool Arguments
Tool Call
Tool Result
```

---

## 最重要认知

> LLM 并没有真的读取文件。

模型只是产生：

```text
请调用 read_file("README.md")
```

真正访问文件系统的是：

```text
micro-pi Runtime
```

---

# 27. V0.4 — Agent Loop

这是整个项目最重要的阶段之一。

---

## 当前问题

复杂任务可能需要：

```text
read
 ↓
read
 ↓
edit
 ↓
bash
 ↓
失败
 ↓
edit
 ↓
bash
```

因此只进行：

```text
一次模型调用
```

已经不够。

---

## 最小 Agent Loop

核心思想：

```python
while True:
    response = call_model(messages)

    if response.tool_call:
        result = execute_tool(response.tool_call)
        messages.append(result)
        continue

    break
```

---

## 核心概念

学习：

```text
Agent Loop
Model Turn
Tool Call
Tool Result
Continuation
Final Answer
```

---

## 必须理解

```text
Agent
≠
LLM
```

最简单可以理解成：

```text
Agent

=
LLM
+
Context
+
Tools
+
Runtime
+
Loop
```

---

# 28. V0.5 — Tool Registry

## 当前问题

Tool 很少时：

```python
if name == "read":
    ...

if name == "bash":
    ...
```

可以接受。

但随着 Tool 增多：

```text
read
write
edit
bash
search
...
```

代码会越来越混乱。

---

## 引入

```text
Tool Registry
```

结构：

```text
Agent
  │
  ▼
Tool Registry
  │
  ├── read
  ├── write
  ├── edit
  └── bash
```

---

## 一个 Tool 至少包含

```text
name
description
parameters
execute()
```

---

## 核心概念

学习：

```text
Tool Interface
Tool Registration
Tool Discovery
Tool Dispatch
Tool Execution
```

---

# 29. V0.6 — Mini Coding Agent

这一阶段让 `micro-pi` 第一次真正成为 Coding Agent。

增加：

```text
read
write
edit
bash
```

---

## 示例任务

```text
> 给 calculator.py 增加 divide 方法并运行测试
```

Agent：

```text
● read
  calculator.py

● read
  test_calculator.py

● edit
  calculator.py

● bash
  pytest

✗ 1 failed

● edit
  calculator.py

● bash
  pytest

✓ 5 passed

任务完成。
```

---

## 学习重点

理解：

```text
一个 Coding Agent
并不是一个神奇的大模型。
```

它本质上仍然是：

```text
LLM
+
Tool
+
Agent Loop
```

---

# 30. V0.7 — Session

## 当前问题

当前：

```python
messages = []
```

只存在内存。

程序退出：

```text
Conversation 消失
Tool History 消失
Agent State 消失
```

---

## 引入 Session

例如：

```text
sessions/
└── session-001.jsonl
```

保存：

```text
User Message
Assistant Message
Tool Call
Tool Result
```

---

## 核心概念

学习：

```text
Session
Entry
Persistence
Resume
History
```

---

## 重点区分

```text
Session
Context
Memory
```

不是一个概念。

---

# 31. V0.8 — Context Compaction

## 当前问题

Session 可以保存无限历史。

但模型 Context Window 是有限的。

例如：

```text
Message 1
Message 2
...
Message 1000
```

不能永远全部发送。

---

## 引入 Compaction

将：

```text
Old Messages
```

压缩为：

```text
Summary
```

然后构造：

```text
System Prompt
+
Summary
+
Recent Messages
```

---

## 核心概念

学习：

```text
Context Window
Token Budget
Context Construction
Compaction
Summary
```

---

# 32. V0.9 — Skill

## 当前问题

Tool 可以回答：

> Agent 能做什么？

例如：

```text
read
write
bash
```

但不能很好回答：

> Agent 遇到一个任务应该按照什么方法完成？

---

## 引入 Skill

例如：

```text
skills/
└── code-review/
    └── SKILL.md
```

内容可能是：

```text
进行代码 Review 时：

1. 阅读代码 Diff
2. 检查正确性
3. 检查异常处理
4. 检查测试
5. 输出 Findings
```

---

## 重点理解

```text
Tool
= 能做什么

Skill
= 应该怎么做
```

---

# 33. V0.10 — Extension

## 当前问题

如果每增加能力都修改 Agent Core：

```text
Agent Core
├── GitHub
├── Browser
├── Database
├── Review
├── Sandbox
└── ...
```

核心会越来越重。

---

## 引入 Extension

例如：

```text
register_tool()

register_hook()

register_command()
```

形成：

```text
Small Core
+
Extensions
```

---

## 学习重点

理解：

> 为什么好的 Agent Framework 往往强调“小核心 + 可扩展”。

---

# 34. V0.11 — Event & Streaming

## 当前问题

随着 Agent Loop 变复杂，Runtime 中会出现：

```text
model started
tool started
tool completed
model continued
agent completed
```

如果所有地方直接：

```python
print()
```

CLI 和 Runtime 会严重耦合。

---

## 引入 Event

例如：

```text
agent_start
model_start
model_delta
tool_start
tool_end
agent_end
```

结构：

```text
Agent Runtime
      │
      │ events
      ▼
CLI Renderer
      │
      ▼
Terminal
```

---

## 核心概念

学习：

```text
Event
Streaming
Runtime State
Observer
Presentation Layer
```

---

# 35. V0.12 — Sandbox

## 当前问题

当 Agent 可以：

```text
bash
write
edit
```

它就拥有了真实系统操作能力。

模型生成的命令不能默认完全可信。

---

## 引入 Sandbox

结构：

```text
Host
 │
 ▼
Sandbox
 │
 ▼
micro-pi Tools
```

学习：

```text
Filesystem Isolation
Process Isolation
Network Isolation
Resource Limit
Permission Boundary
```

---

# 36. V0.13 — SubAgent

## 当前问题

复杂任务可能同时需要：

```text
Explore
Coding
Testing
Review
```

是否可以把部分任务委托给其他 Agent？

---

## 引入 SubAgent

```text
Main Agent
   │
   ├── Explore Agent
   ├── Test Agent
   └── Review Agent
```

---

## 核心概念

学习：

```text
Delegation
Parent Agent
Child Agent
Context Isolation
Parallel Execution
```

---

# 37. V0.14 — Durable Run

## 当前问题

Agent 执行长任务：

```text
运行到一半
 ↓
进程崩溃
```

是否必须完全重新开始？

---

## 引入

```text
Run
Attempt
Checkpoint
Retry
Resume
Heartbeat
Idempotency
```

状态：

```text
PENDING
 ↓
RUNNING
 ↓
WAITING_TOOL
 ↓
RUNNING
 ↓
SUCCEEDED
```

异常：

```text
RUNNING
 ↓
FAILED
 ↓
RETRY
 ↓
RECOVERING
 ↓
RUNNING
```

这一阶段开始进入：

```text
Production Agent Runtime
```

---

# 38. V1.0 — micro-pi Core

最终核心结构可能演化为：

```text
micro-pi

├── Provider
├── Message
├── Context
├── Agent Loop
├── Tool Registry
├── Coding Tools
├── Session
├── Compaction
├── Skill
├── Extension
├── Event
├── CLI Renderer
├── Sandbox
└── SubAgent
```

但这些模块不会一次出现。

它们必须从前面的学习过程中逐渐成长出来。

---

# 39. Runtime 与 CLI 分层

随着项目成长，需要逐渐形成：

```text
┌──────────────────────────────┐
│        micro-pi CLI          │
│                              │
│ input                        │
│ render                       │
│ keyboard                     │
│ commands                     │
└──────────────┬───────────────┘
               │
               │ UserInput / Events
               ▼
┌──────────────────────────────┐
│       Agent Runtime          │
│                              │
│ Agent Loop                   │
│ Context                      │
│ Tool Registry                │
│ Session                      │
└──────────────┬───────────────┘
               │
               ▼
             Model
```

核心理解：

> Agent Runtime 不应该依赖 CLI。

未来理论上可以替换成：

```text
Web
App
API
```

而 Agent Core 不需要重写。

---

# 40. 正式教程章节规划

第一轮学习完成后，将项目整理为：

```text
Chapter 01
让 micro-pi 第一次和 LLM 对话

Chapter 02
模型为什么能记住上一句话？

Chapter 03
给 micro-pi 第一个 Tool

Chapter 04
Agent 最核心的代码：while 循环

Chapter 05
Tool 多了怎么办：Tool Registry

Chapter 06
让 micro-pi 成为 Coding Agent

Chapter 07
程序关闭后怎么继续：Session

Chapter 08
Context 放不下怎么办：Compaction

Chapter 09
Skill 到底是什么？

Chapter 10
为什么需要 Extension？

Chapter 11
Agent 的运行过程如何展示：Event

Chapter 12
为什么 Agent 需要 Sandbox？

Chapter 13
一个 Agent 不够怎么办：SubAgent

Chapter 14
Agent 崩了怎么办：Durable Run

Chapter 15
重新阅读 Pi：我们到底实现了什么？
```

---

# 41. 每章统一结构

正式教程每章尽量保持：

```text
01. 上一版本是什么？

02. 现在遇到什么问题？

03. 为什么会出现？

04. 我们需要什么新能力？

05. 用大白话解释概念

06. 手写最小代码

07. 运行 micro-pi

08. 在 CLI 中观察结果

09. 画执行流程图

10. Debug / 常见坑

11. 总结

12. Pi 是怎么做的？
```

---

# 42. 代码规模原则

教学代码应尽可能少。

原则：

> 如果一个概念需要大量代码才能解释，就继续拆。

理想状态：

```text
V0.1
几十行

V0.2
只增加 Conversation

V0.3
只增加 Tool

V0.4
只增加 Agent Loop
```

而不是：

```text
第一章
20 个目录
50 个类
数千行代码
```

---

# 43. 项目目录演进

## 初期

```text
learn-pi/
├── src/
│   └── micro_pi/
│       └── main.py
│
├── learning-notes/
├── README.md
└── PRD.md
```

---

## 中期

```text
learn-pi/
├── src/
│   └── micro_pi/
│       ├── main.py
│       ├── llm.py
│       ├── agent.py
│       │
│       └── tools/
│           ├── read.py
│           ├── write.py
│           ├── edit.py
│           └── bash.py
│
├── learning-notes/
├── examples/
├── tests/
├── README.md
└── PRD.md
```

---

## 后期

```text
learn-pi/
├── src/
│   └── micro_pi/
│       ├── cli/
│       │   └── app.py
│       │
│       ├── agent/
│       │   ├── agent.py
│       │   └── loop.py
│       │
│       ├── ai/
│       │   └── provider.py
│       │
│       ├── tools/
│       │   ├── registry.py
│       │   ├── read.py
│       │   ├── write.py
│       │   ├── edit.py
│       │   └── bash.py
│       │
│       ├── session/
│       │   └── session.py
│       │
│       ├── context/
│       │   └── compaction.py
│       │
│       ├── events/
│       ├── skills/
│       └── extensions/
│
├── chapters/
├── learning-notes/
├── examples/
├── tests/
├── README.md
└── PRD.md
```

---

# 44. Learning Notes

开发过程中建立：

```text
learning-notes/
```

它不是正式教程。

只负责记录真实学习过程。

每阶段建议记录：

```text
我原来以为是什么？

实际上是什么？

为什么我会理解错？

哪一部分最难理解？

我踩过什么坑？

哪个例子让我突然理解？

如果让我给另一个小白讲，
我会怎么解释？
```

这些内容将成为后续教程最重要的原始素材之一。

---

# 45. AI Coding 使用原则

项目允许使用 AI。

但需要区分两类代码。

---

## 45.1 高学习价值代码

优先自己手写：

```text
Message

Conversation

Tool Calling

Tool Result

Agent Loop

Tool Registry

Context Construction

Session

Compaction

Skill Loading

Event Flow
```

---

## 45.2 低学习价值工程代码

可以更多使用 AI：

```text
CLI 参数

简单配置加载

日志格式

Mock

测试辅助

重复的数据结构

简单辅助函数

发布配置
```

---

# 46. 推荐 AI 使用方式

优先询问：

```text
解释这个报错，不要直接改代码。

给我提示，不要直接给答案。

Review 我的代码，只告诉我问题。

为什么这里需要这样设计？

如果删除这段代码会发生什么？

问我几个问题检查我是否真正理解。
```

避免长期依赖：

```text
帮我完整实现这个功能。
```

项目原则：

> AI 可以减少重复劳动，但不能替代理解。

---

# 47. 第一阶段暂不做

为了保持核心学习路径干净，前期暂不重点实现：

- Web UI
- Mobile App
- RAG
- Vector Database
- 大量 MCP
- Kubernetes
- Redis
- PostgreSQL
- Celery
- 微服务
- 多租户
- Agent Marketplace
- 大规模 Multi-Agent
- 企业管理后台
- 完整 Benchmark 平台
- 大量 Provider 适配

原因：

> 这些东西不是 Agent Core。

---

# 48. 第一阶段验收标准

完成 Agent Core 学习后，应能够脱离代码清楚解释：

```text
Provider 是什么？

Model 是什么？

Message 是什么？

Context 是什么？

模型为什么能多轮对话？

Tool Calling 是什么？

Tool Call 是谁生成的？

Tool 是谁真正执行的？

Tool Result 为什么要回给模型？

Agent Loop 为什么存在？

Agent Loop 什么时候结束？

Agent 和 LLM 有什么区别？

Tool Registry 为什么存在？

Session 是什么？

Session 和 Context 有什么区别？

Compaction 为什么需要？

Skill 和 Tool 有什么区别？

Extension 为什么存在？

Event 为什么需要？
```

---

# 49. 必须能够独立画出的流程

完成核心阶段后，应能画出：

```text
User
 │
 ▼
micro-pi CLI
 │
 ▼
Agent Runtime
 │
 ▼
Context
 │
 ▼
LLM
 │
 ├───────────────┐
 │               │
 │ Final Answer  │ Tool Call
 │               ▼
 │         Tool Registry
 │               │
 │               ▼
 │              Tool
 │               │
 │               ▼
 │          Tool Result
 │               │
 └───────────────┘
        ↓
      LLM
        ↓
 Final Answer
```

并能解释其中每一条箭头。

---

# 50. 第一阶段最终能力

在不依赖大型 Agent Framework 的情况下，能够自己实现：

```text
Terminal CLI
+
LLM Conversation
+
Tool Calling
+
Agent Loop
+
Tool Registry
+
read / write / edit / bash
+
Session
```

形成一个真正可以使用的：

```text
micro-pi
```

---

# 51. 最终用户体验

长期目标：

```bash
micro-pi
```

进入：

```text
micro-pi

minimal · transparent · educational


~/projects/demo

> 帮我检查这个项目的测试问题

● read
  README.md

● read
  src/calculator.py

● read
  tests/test_calculator.py

● bash
  pytest

✗ 1 failed

● edit
  src/calculator.py

● bash
  pytest

✓ 8 passed

问题已经修复，全部测试通过。

>
```

---

# 52. CLI 命令原则

后续可以逐渐增加少量命令：

```text
/help

/new

/resume

/model

/context

/exit
```

但不追求大量 Command。

原则：

> 如果命令不是核心需要，就不增加。

---

# 53. Python 包与命名规划

当前建议：

```text
项目名称
learn-pi

GitHub Repository
learn-pi

Python Module
micro_pi

CLI Command
micro-pi
```

PyPI 的最终 Distribution Name：

```text
发布阶段再确定
```

避免现在为了包名提前限制项目设计。

---

# 54. 发布后的理想体验

未来用户通过 pip 安装包：

```bash
pip install <最终 PyPI 包名>
```

然后直接：

```bash
micro-pi
```

进入 Agent。

因此：

```text
pip package
和
CLI command
```

不要求完全同名。

---

# 55. 项目成功标准

`learn-pi` 的成功标准不是：

```text
功能比 Pi 更多
```

也不是：

```text
代码量很大
```

而是：

> 一个 Agent 小白可以沿着项目从 Chapter 01 开始，逐渐理解 Agent，并最终能够自己解释和实现 Agent Core。

同时项目作者本人能够从：

```text
Agent Framework 使用者
```

成长为：

```text
Agent Runtime 理解者
```

再进一步成长为：

```text
Agent Architecture 开发者
```

---

# 56. 项目核心价值

## 对作者

通过亲手实现：

```text
LLM
Tool
Loop
Context
Session
Skill
Runtime
```

真正建立 Agent 底层认知。

---

## 对学习者

不需要先阅读复杂框架。

而是：

```text
少量代码
 ↓
运行
 ↓
看到现象
 ↓
理解原因
 ↓
增加一个能力
```

一步一步学习。

---

## 对开源项目

形成一个：

```text
Minimal
Transparent
Terminal-native
Educational
```

的 Agent 学习项目。

---

## 对求职

最终项目不仅能够体现：

```text
“我会使用 Agent Framework”
```

更能够体现：

```text
我理解 Agent Loop

我理解 Tool Calling

我理解 Context

我理解 Session

我理解 Tool System

我理解 Skill

我理解 Runtime

我理解 Agent 如何逐渐走向生产环境
```

---

# 57. 项目设计原则总结

整个 `learn-pi` 长期坚持：

```text
先问题
后概念

先现象
后原理

先手写
后框架

先最小
后抽象

先透明
后封装

先 Agent Core
后 Production Runtime

先真正学会
再教别人
```

---

# 58. 当前项目阶段

当前处于：

```text
Phase 1

Learn Agent
```

第一目标：

> 作者本人真正学会 Agent。

---

# 59. 当前开发版本

当前从：

```text
V0.1
```

开始。

唯一目标：

> **让 micro-pi 在终端中完成第一次最简单、最透明的 LLM 对话。**

此阶段只需要：

```text
Terminal Input
       ↓
LLM Request
       ↓
LLM Response
       ↓
Terminal Output
```

暂时不引入：

```text
Tool

Agent Loop

Session

Skill

Sandbox

SubAgent
```

---

# 60. 当前最小产品形态

第一版：

```bash
micro-pi
```

界面：

```text
micro-pi

> hello

Hello!

>
```

内部：

```text
input()
   ↓
call_model()
   ↓
print()
```

如果能够完全理解这三步：

> V0.1 就成功了。

下一阶段再增加：

```text
Conversation
```

而不是提前增加复杂能力。

---

# 61. 最终愿景

最终希望 `learn-pi` 能让一个从未真正理解 Agent 的开发者经历：

```text
第一次调用 LLM
       ↓
第一次理解 Context
       ↓
第一次看见 Tool Call
       ↓
第一次亲手写 Agent Loop
       ↓
第一次实现 Coding Agent
       ↓
第一次理解 Session
       ↓
第一次理解 Skill
       ↓
第一次理解 Agent Framework
       ↓
开始真正读懂 Pi
       ↓
继续进入 Production Agent Runtime
```

最终不再觉得：

```text
Agent 是魔法。
```

而能够清楚地知道：

> **Agent 就是由一系列可以理解、可以实现、可以观察的简单机制逐渐组合起来的系统。**