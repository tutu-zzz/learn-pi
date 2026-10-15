# micro-pi 版本学习指南

[← 返回项目首页](../README.md)

这里保存 `micro-pi` 从一次 LLM 调用逐步成长为终端 Agent 的完整学习路径。每个版本只引入一个主要能力，并以上一版代码为基线继续手写。

## 如何使用

1. 展开当前版本，先阅读开头的**完整系统运转流程**。
2. 先理解“上一版的问题”，再阅读本版的解决方法。
3. 按“动手改造”的顺序修改代码，不要直接复制最终文件。
4. 完成运行与验收后，再打开完整代码快照进行核对。
5. 代码中的 `[V0.x 新增]` 和 `[V0.x 修改]` 注释也可以帮助定位差异。

> V0.1–V0.13 已完成并通过测试。所有命令均从项目根目录运行，对话版本输入 `/exit` 可以结束程序。

## 已完成版本

<details>
<summary><strong>📌 V0.1 — First LLM Call：一次模型请求发生了什么？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    A["启动程序（本版新增）"] --> B["加载 .env（本版新增）"]
    B --> C["读取 Base URL、Model、API Key（本版新增）"]
    C --> D["读取终端输入（本版新增）"]
    D --> E["构造 Messages（本版新增）"]
    E --> F["发送 HTTP 请求（本版新增）"]
    F --> G["LLM"]
    G --> H["解析 Response（本版新增）"]
    H --> I["输出回答（本版新增）"]
    I --> J["程序结束"]
~~~

**上一版已经完成什么**

这是第一个版本，没有上一版。起点是一个空白的 `main.py`。

**引入问题**

我们已经可以在网页或现成客户端中与模型对话，但还不知道终端里的一句话是如何变成 HTTP 请求，又如何从 JSON 响应中取回回答。

**针对问题的解决方法**

暂时不引入 SDK、Tool 或 Agent Loop，只手动完成最小链路：

~~~text
读取配置 → 构造请求 → 调用模型 → 解析回答
~~~

**动手改造**

**步骤 1：新增依赖与模型配置**

在空白 `main.py` 顶部新增：

~~~python
import os

import requests
from dotenv import load_dotenv


load_dotenv()

base_url = os.getenv("MICRO_PI_BASE_URL")
model = os.getenv("MICRO_PI_MODEL")
api_key = os.getenv("MICRO_PI_API_KEY")

if not base_url or not model or not api_key:
    raise RuntimeError("模型配置不完整")
~~~

这一步只负责从本地环境读取配置，不要在代码里写真实 API Key。

**步骤 2：新增请求地址和请求头**

放在配置检查之后：

~~~python
url = f"{base_url.rstrip('/')}/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
~~~

**步骤 3：读取输入并构造 Messages**

~~~python
user_message = input("> ")

request_data = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message},
    ],
}
~~~

**步骤 4：发送请求并提取回答**

~~~python
response = requests.post(
    url,
    headers=headers,
    json=request_data,
    timeout=20,
)
response.raise_for_status()

data = response.json()
answer = data["choices"][0]["message"]["content"]
print(f"Answer: {answer}")
~~~

**改造后的关键变化**

| 类型 | 位置 | 结果 |
| --- | --- | --- |
| 新增 | 文件顶部 | 加载模型配置 |
| 新增 | 配置之后 | 准备 URL 和 Headers |
| 新增 | 请求之前 | 将终端输入转换为 Messages |
| 新增 | 文件末尾 | 发送请求并输出回答 |

**运行与验收**

~~~bash
python learning-versions/01_v0.1_first_llm_call/main.py
~~~

输入任意问题，确认模型能够回答，同时终端没有输出 API Key。

**完整代码入口：** [main.py](01_v0.1_first_llm_call/main.py)

</details>

<details>
<summary><strong>📌 V0.2 — Conversation：模型为什么能记住前文？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    A["启动程序"] --> B["加载模型配置"]
    B --> C["创建 messages（本版新增）"]
    C --> D["读取用户输入"]
    D --> E{"输入是否为 /exit？"}
    E -- "是" --> F["程序结束"]
    E -- "否" --> G["追加 user 消息（本版新增）"]
    G --> H["发送完整 messages"]
    H --> I["LLM"]
    I --> J["追加 assistant 消息（本版新增）"]
    J --> K["输出回答"]
    K --> D
~~~

**上一版已经完成什么**

V0.1 已能完成一次“终端输入 → LLM → 终端输出”，但程序回答一次后立即结束。

**引入问题**

如果第一轮告诉模型“我叫小明”，第二轮再问“我叫什么”，V0.1 无法回答，因为每次请求只包含当前输入，没有之前的对话。

**针对问题的解决方法**

在循环外维护一个 `messages` 列表。每轮把 user 和 assistant 消息都追加进去，并在下一次请求时发送完整历史。

**动手改造**

**步骤 1：在读取用户输入之前新增消息历史**

原来没有长期存在的消息列表。现在在请求循环之前新增：

~~~python
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant.",
    }
]
~~~

必须放在循环外，否则每轮都会重新创建，历史仍然会丢失。

**步骤 2：将单次输入替换为外层对话循环**

原来的代码：

~~~python
user_message = input("> ")

request_data = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message},
    ],
}
~~~

替换为：

~~~python
while True:
    user_message = input("> ")

    if user_message == "/exit":
        break

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    request_data = {
        "model": model,
        "messages": messages,
    }
~~~

**步骤 3：把模型回答也保存到历史**

原来的代码只打印回答：

~~~python
answer = data["choices"][0]["message"]["content"]
print(f"Answer: {answer}")
~~~

将请求和响应代码缩进到 `while` 中，并在打印前新增：

~~~python
answer = data["choices"][0]["message"]["content"]

messages.append(
    {
        "role": "assistant",
        "content": answer,
    }
)

print(f"Answer: {answer}")
~~~

**改造后的关键变化**

| 类型 | 位置 | 结果 |
| --- | --- | --- |
| 新增 | 对话循环之前 | 创建共享的 `messages` |
| 替换 | 原单次输入 | 改为持续接收输入的 `while` |
| 新增 | 用户输入之后 | 保存 user 消息 |
| 新增 | 模型响应之后 | 保存 assistant 消息 |
| 新增 | 循环开头 | 使用 `/exit` 结束会话 |

**运行与验收**

~~~bash
python learning-versions/02_v0.2_conversation/main.py
~~~

依次输入：

~~~text
我叫小明，请记住。
我叫什么？
~~~

模型应回答“小明”。退出程序再重新启动后，历史会消失——这是后续 Session 要解决的问题。

**完整代码入口：** [main.py](02_v0.2_conversation/main.py)

</details>

<details>
<summary><strong>📌 V0.3 — Tool Calling：模型如何提出工具请求？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    A["启动程序"] --> B["加载配置并创建 messages"]
    B --> C["读取用户输入"]
    C --> D{"输入是否为 /exit？"}
    D -- "是" --> E["程序结束"]
    D -- "否" --> F["追加 user 消息"]
    F --> G["第一次调用 LLM"]
    G --> H{"是否生成 Tool Call？"}
    H -- "否" --> I["保存并输出普通回答"]
    I --> C
    H -- "是" --> J["解析工具名和参数（本版新增）"]
    J --> K["Python 执行 read_file（本版新增）"]
    K --> L["追加 Tool Result（本版新增）"]
    L --> M["第二次调用 LLM"]
    M --> N["保存并输出 Final Answer"]
    N --> C
~~~

**上一版已经完成什么**

V0.2 可以多轮对话，但模型只能根据请求中已有的文本回答。

**引入问题**

当用户询问“README 里写了什么”时，模型并不能直接访问本地文件。模型可能猜测，但拿不到真实内容。

**针对问题的解决方法**

给模型一份 Tool Schema。模型只负责生成结构化 Tool Call，Python Runtime 负责真正读取文件，再把 Tool Result 返回模型生成最终回答。

**动手改造**

**步骤 1：新增解析工具参数和读取文件所需的依赖**

在导入区新增：

~~~python
import json
from pathlib import Path
~~~

**步骤 2：在 `messages` 之后新增 Tool Schema**

~~~python
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取项目中的 README.md 文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "enum": ["README.md"],
                        "description": "文件路径",
                    }
                },
                "required": ["path"],
            },
        },
    }
]
~~~

Tool Schema 只是给模型看的说明，还没有执行文件读取。

**步骤 3：新增真正执行工具的函数**

放在 Tool Schema 之后：

~~~python
def read_file(path):
    if path != "README.md":
        return "Error: V0.3只允许读取 README.md"
    return Path(path).read_text(encoding="utf-8")
~~~

**步骤 4：把直接请求封装为 `call_model()`**

原来的循环中直接调用 `requests.post()`。将模型请求提取为：

~~~python
def call_model(messages):
    request_data = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }

    response = requests.post(
        url,
        headers=headers,
        json=request_data,
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]
~~~

**步骤 5：将普通回答流程替换为 Tool Calling 流程**

在保存 user 消息之后，替换原来的请求与输出代码：

~~~python
assistant_message = call_model(messages)
messages.append(assistant_message)

tool_calls = assistant_message.get("tool_calls")

if not tool_calls:
    print(f"Answer: {assistant_message['content']}")
    continue

tool_call = tool_calls[0]
tool_name = tool_call["function"]["name"]
tool_arguments = json.loads(tool_call["function"]["arguments"])

if tool_name != "read_file":
    raise RuntimeError(f"未知工具: {tool_name}")

tool_result = read_file(tool_arguments["path"])

messages.append(
    {
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": tool_result,
    }
)

final_message = call_model(messages)
messages.append(final_message)
print(f"最终回答 Final Message: {final_message['content']}")
~~~

**改造后的关键变化**

| 类型 | 位置 | 结果 |
| --- | --- | --- |
| 新增 | 导入区 | 支持 JSON 参数和文件读取 |
| 新增 | `messages` 之后 | 告诉模型 `read_file` 的格式 |
| 新增 | Tool Schema 之后 | 由 Python 真正读取文件 |
| 替换 | 直接 HTTP 调用 | 使用 `call_model()` |
| 替换 | 普通输出流程 | Tool Call → Tool Result → Final Answer |

**运行与验收**

~~~bash
python learning-versions/03_v0.3_tool_calling/main.py
~~~

输入“请读取 README.md 并告诉我项目名称”。确认终端能看到 Tool Call、真实文件内容和最终回答。

**完整代码入口：** [main.py](03_v0.3_tool_calling/main.py)

</details>

<details>
<summary><strong>📌 V0.4 — Agent Loop：Agent 为什么需要循环？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    A["启动程序并加载配置"] --> B["创建 messages 和 Tool Schema"]
    B --> C["读取用户输入"]
    C --> D{"输入是否为 /exit？"}
    D -- "是" --> E["程序结束"]
    D -- "否" --> F["追加 user 消息"]
    F --> G["进入 Agent Loop（本版新增）"]
    G --> H["调用 LLM"]
    H --> I["保存 assistant message"]
    I --> J{"是否有 Tool Call？"}
    J -- "否" --> K["输出 Final Answer"]
    K --> C
    J -- "是" --> L["遍历本轮全部 Tool Calls（本版修改）"]
    L --> M["解析工具和参数"]
    M --> N["执行 read_file"]
    N --> O["追加 Tool Result"]
    O --> G
~~~

**上一版已经完成什么**

V0.3 能完成一次 Tool Call，但代码假设流程一定是“第一次调用工具、第二次给出答案”。

**引入问题**

真实任务可能需要连续读取多个文件或多次修正操作。固定调用两次无法表达“模型还想继续调用工具”的情况。

**针对问题的解决方法**

在外层对话循环内部再增加一个 Agent Loop。每一轮都让模型决定下一步：有 Tool Call 就执行并继续，没有 Tool Call 才结束当前任务。

**动手改造**

**步骤 1：保留外层对话循环**

V0.2 的 `while True` 继续负责读取不同用户任务，不需要删除。把它理解为：

~~~python
while True:
    user_message = input("> ")
    # 处理 /exit
    # 追加 user 消息
    # 这里即将进入本轮任务的 Agent Loop
~~~

**步骤 2：删除固定的“第一次调用 / 第二次调用”代码**

V0.3 中从下面这行开始的固定流程：

~~~python
assistant_message = call_model(messages)
~~~

一直到：

~~~python
final_message = call_model(messages)
print(f"最终回答 Final Message: {final_message['content']}")
~~~

整体替换为内层循环。

**步骤 3：新增 Agent Loop**

放在追加 user 消息之后：

~~~python
while True:
    assistant_message = call_model(messages)
    messages.append(assistant_message)

    tool_calls = assistant_message.get("tool_calls")

    if not tool_calls:
        print(f"Answer: {assistant_message['content']}")
        break

    for tool_call in tool_calls:
        tool_name = tool_call["function"]["name"]
        tool_arguments = json.loads(
            tool_call["function"]["arguments"]
        )

        if tool_name != "read_file":
            raise RuntimeError(f"未知工具: {tool_name}")

        tool_result = read_file(tool_arguments["path"])

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": tool_result,
            }
        )
~~~

注意两个 `while True` 的职责不同：

- 外层循环：等待下一条用户输入。
- 内层循环：持续完成当前任务。

**改造后的关键变化**

| 类型 | 位置 | 结果 |
| --- | --- | --- |
| 删除 | V0.3 固定两次调用 | 不再预设模型调用次数 |
| 新增 | user 消息之后 | 建立内层 Agent Loop |
| 修改 | 单个 `tool_calls[0]` | 遍历本轮全部 Tool Call |
| 新增 | 无 Tool Call 分支 | 结束当前任务并回到外层循环 |

**运行与验收**

~~~bash
python learning-versions/04_v0.4_agent_loop/main.py
~~~

让模型读取 README 并回答。观察它有 Tool Call 时继续循环，没有 Tool Call 时才输出最终回答。

**完整代码入口：** [main.py](04_v0.4_agent_loop/main.py)

</details>

<details>
<summary><strong>📌 V0.5 — Tool Registry：工具多了以后如何管理？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    subgraph START["启动阶段"]
        A["启动程序"] --> B["加载模型配置"]
        B --> C["创建 Tool Registry（本版新增）"]
        C --> D["从 Registry 生成 Tool Schema（本版修改）"]
        D --> E["创建 messages"]
    end

    subgraph CHAT["外层对话循环"]
        E --> F["读取用户输入"]
        F --> G{"输入是否为 /exit？"}
        G -- "是" --> H["程序结束"]
        G -- "否" --> I["追加 user 消息"]
    end

    subgraph AGENT["Agent Loop"]
        I --> J["调用 LLM"]
        J --> K["保存 assistant message"]
        K --> L{"是否有 Tool Call？"}
        L -- "否" --> M["输出 Final Answer"]
        M --> F
        L -- "是" --> N["解析工具名和参数"]
    end

    subgraph TOOL["Tool Runtime"]
        N --> O["按名称查询 Registry（本版新增）"]
        O --> P{"是否找到工具？"}
        P -- "否" --> Q["抛出未知工具错误"]
        P -- "是" --> R["取得 execute 并执行（本版修改）"]
        R --> S["追加 Tool Result"]
    end

    S --> J
~~~

**上一版已经完成什么**

V0.4 已有完整 Agent Loop，但 Tool Schema、工具函数和执行分支彼此分散，而且仍然硬编码只认识 `read_file`。

**引入问题**

如果继续加入 `write_file`、`edit_file`、`bash`，就需要同时修改 Schema 和大量 `if/elif`。工具越多，Runtime 越难维护。

**针对问题的解决方法**

建立 Tool Registry。每个工具用一个注册项同时保存给模型看的 `description / parameters` 和给 Runtime 用的 `execute`。

**动手改造**

**步骤 1：用 Registry 集中注册 `read_file`**

原来的 `tools` 直接写死了完整 Tool Schema。先保留 `read_file()`，在它之后新增：

~~~python
tool_registry = {
    "read_file": {
        "description": "读取项目中的 README.md 文件",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "enum": ["README.md"],
                    "description": "文件路径",
                }
            },
            "required": ["path"],
        },
        "execute": read_file,
    }
}
~~~

**步骤 2：替换手写 Tool Schema**

原来的代码：

~~~python
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取项目中的 README.md 文件",
            "parameters": {
                # ...
            },
        },
    }
]
~~~

替换为从 Registry 生成：

~~~python
tools = [
    {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }
    for tool_name, tool in tool_registry.items()
]
~~~

**步骤 3：替换硬编码工具分发**

原来的代码：

~~~python
if tool_name != "read_file":
    raise RuntimeError(f"未知工具: {tool_name}")

tool_result = read_file(tool_arguments["path"])
~~~

替换为：

~~~python
tool = tool_registry.get(tool_name)
if not tool:
    raise RuntimeError(f"未知工具: {tool_name}")

tool_result = tool["execute"](**tool_arguments)
~~~

`**tool_arguments` 把模型生成的字典拆成关键字参数，因此 Registry 中的函数可以有不同参数。

**改造后的关键变化**

| 类型 | 位置 | 结果 |
| --- | --- | --- |
| 新增 | 工具函数之后 | 建立 Tool Registry |
| 替换 | 原 `tools` 列表 | 从 Registry 自动生成 Schema |
| 替换 | Agent Loop 工具分发 | 按名称找到并执行函数 |

**运行与验收**

~~~bash
python learning-versions/05_v0.5_tool_registry/main.py
~~~

再次读取 README。结果应与 V0.4 相同，但 Tool Schema 和 Runtime 已共享同一份注册信息。

**完整代码入口：** [main.py](05_v0.5_tool_registry/main.py)

</details>

<details>
<summary><strong>📌 V0.6 — Mini Coding Agent：如何真正操作项目？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    subgraph START["启动阶段"]
        A["启动程序"] --> B["加载模型配置"]
        B --> C["确定 Workspace（本版新增）"]
        C --> D["注册 read / write / edit / bash（本版修改）"]
        D --> E["生成 Tool Schema"]
        E --> F["创建 messages"]
    end

    subgraph CHAT["外层对话循环"]
        F --> G["读取编码任务"]
        G --> H{"输入是否为 /exit？"}
        H -- "是" --> I["程序结束"]
        H -- "否" --> J["追加 user 消息"]
    end

    subgraph AGENT["Agent Loop"]
        J --> K["调用 LLM"]
        K --> L["保存 assistant message"]
        L --> M{"是否有 Tool Call？"}
        M -- "否" --> N["输出 Final Answer"]
        N --> G
        M -- "是" --> O["解析工具名和参数"]
        O --> P["Registry 查找工具"]
    end

    subgraph TOOL["Tool Runtime"]
        P --> Q{"选择哪种工具？"}
        Q -- "read / write / edit" --> R["resolve_path 检查路径（本版新增）"]
        R --> S["执行文件操作"]
        Q -- "bash" --> T["在 Workspace 中执行系统 Shell"]
        S --> U{"执行是否成功？"}
        T --> U
        U -- "是" --> V["返回真实结果"]
        U -- "否" --> W["返回 Error Tool Result（本版修改）"]
    end

    V --> X["追加 Tool Result"]
    W --> X
    X --> K
~~~

**上一版已经完成什么**

V0.5 已能注册和分发工具，但 Registry 中只有一个受限的 `read_file`。

**引入问题**

Coding Agent 不仅要读取文件，还要创建、修改文件并运行项目命令。直接开放文件路径和 Shell 又会引入越界访问与执行失败的问题。

**针对问题的解决方法**

把当前启动目录作为 Workspace，为文件工具统一增加路径解析，再向 Registry 注册 `read / write / edit / bash`。工具异常不再让 Agent 崩溃，而是作为 Tool Result 返回模型。

**动手改造**

**步骤 1：新增 `subprocess`**

在导入区新增：

~~~python
import subprocess
~~~

**步骤 2：新增 Workspace 和路径检查**

放在工具函数之前：

~~~python
workspace = Path.cwd().resolve()


def resolve_path(path):
    target = (workspace / path).resolve()
    if target != workspace and workspace not in target.parents:
        raise ValueError("路径超出当前项目范围")
    return target
~~~

**步骤 3：替换 `read_file()`，并新增三个工具函数**

原来的 `read_file()` 只允许 `README.md`。替换为：

~~~python
def read_file(path):
    return resolve_path(path).read_text(encoding="utf-8")
~~~

紧接着新增：

~~~python
def write_file(path, content):
    target = resolve_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"已写入文件：{path}"


def edit_file(path, old_text, new_text):
    target = resolve_path(path)
    content = target.read_text(encoding="utf-8")

    if not old_text or old_text not in content:
        return "Error: 未找到需要替换的内容"

    content = content.replace(old_text, new_text, 1)
    target.write_text(content, encoding="utf-8")
    return f"已编辑文件：{path}"


def run_bash(command):
    result = subprocess.run(
        command,
        shell=True,
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return (
        f"Exit code 退出码: {result.returncode}\n"
        f"stdout 标准输出：{result.stdout}\n"
        f"stderr 标准错误：{result.stderr}\n"
    )
~~~

**步骤 4：将单工具 Registry 替换为四个 Coding Tools**

四个注册项的对应关系：

| 工具名 | 必填参数 | `execute` |
| --- | --- | --- |
| `read` | `path` | `read_file` |
| `write` | `path, content` | `write_file` |
| `edit` | `path, old_text, new_text` | `edit_file` |
| `bash` | `command` | `run_bash` |

每个注册项继续使用 V0.5 的统一结构：

~~~python
tool_registry = {
    "read": {
        "description": "读取当前项目中的文本文件",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "相当于当前项目的文件路径",
                }
            },
            "required": ["path"],
        },
        "execute": read_file,
    },
    # 按相同结构继续注册 write、edit、bash
}
~~~

完整参数定义请在手写后与本版快照核对。

**步骤 5：为工具执行增加异常回传**

原来的代码：

~~~python
tool_result = tool["execute"](**tool_arguments)
~~~

替换为：

~~~python
try:
    tool_result = tool["execute"](**tool_arguments)
except Exception as e:
    tool_result = f"Error: {e}"
~~~

这样模型能读到错误并调整下一步，而不是直接终止进程。

**改造后的关键变化**

| 类型 | 位置 | 结果 |
| --- | --- | --- |
| 新增 | 工具函数之前 | 定义 Workspace 和路径边界 |
| 修改 | `read_file()` | 支持读取任意工作区文本文件 |
| 新增 | 工具函数区 | 增加 write、edit、bash |
| 替换 | Tool Registry | 注册四个 Coding Tools |
| 修改 | Agent Loop | 将异常转换为 Tool Result |

**运行与验收**

~~~bash
python learning-versions/06_v0.6_mini_coding_agent/main.py
~~~

可以输入：

~~~text
创建 hello.py，让它输出 Hello, micro-pi!，然后运行它。
~~~

观察 Agent 是否依次调用 write 和 bash，并根据真实执行结果回答。

> **安全提示：** `bash` 仍直接使用系统 Shell。本版不是 Sandbox，只应在测试目录或可恢复环境中运行。

**完整代码入口：** [main.py](06_v0.6_mini_coding_agent/main.py)

</details>

<details>
<summary><strong>📌 V0.7 — Session：程序重启后如何继续对话？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    subgraph START["启动阶段"]
        A["启动程序"] --> B["加载模型配置"]
        B --> C["读取 Session JSONL（本版新增）"]
        C --> D["恢复完整 messages（本版修改）"]
        D --> E["确定 Workspace"]
        E --> F["注册 Coding Tools"]
        F --> G["生成 Tool Schema"]
    end

    subgraph CHAT["外层对话循环"]
        G --> H["读取用户输入"]
        H --> I{"输入是否为 /exit？"}
        I -- "是" --> J["程序退出"]
        J --> K["下次启动重新读取 JSONL"]
        K --> C
        I -- "否" --> L["add_message 保存 user（本版修改）"]
    end

    subgraph AGENT["Agent Loop"]
        L --> M["调用 LLM"]
        M --> N["add_message 保存 assistant（本版修改）"]
        N --> O{"是否有 Tool Call？"}
        O -- "否" --> P["输出 Final Answer"]
        P --> H
        O -- "是" --> Q["Registry 查找工具"]
    end

    subgraph TOOL["Tool Runtime"]
        Q --> R["执行 read / write / edit / bash"]
        R --> S["得到真实结果或 Error"]
        S --> T["add_message 保存 Tool Result（本版修改）"]
    end

    T --> M
~~~

**上一版已经完成什么**

V0.6 已能完成多步编码任务，但 `messages` 只存在于当前 Python 进程。

**引入问题**

程序退出后，对话、Tool Call 和 Tool Result 全部消失。下一次启动时，模型无法继续上次任务。

**针对问题的解决方法**

将每条非 system 消息追加到 JSONL。启动时逐行读取 JSONL 恢复 `messages`；运行时通过统一的 `add_message()` 同时写内存和磁盘。

**动手改造**

**步骤 1：新增 Session 路径和 System Message**

放在 `headers` 之后：

~~~python
session_path = Path("sessions/session-002.jsonl")

system_messages = {
    "role": "system",
    "content": (
        "You are a concise coding assistant. "
        "Answer ordinary conversation directly. "
        "Use tools only when the user explicitly asks you to operate on files or run commands. "
        "Session persistence is handled automatically by the runtime."
    ),
}
~~~

**步骤 2：新增加载和保存函数**

~~~python
def load_session():
    history = [system_messages]

    if not session_path.exists():
        return history

    with session_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                history.append(json.loads(line.strip()))
    return history


def add_message(message):
    messages.append(message)

    session_path.parent.mkdir(parents=True, exist_ok=True)

    with session_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n")
~~~

**步骤 3：替换内存消息初始化**

原来的代码：

~~~python
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant.",
    }
]
~~~

替换为：

~~~python
messages = load_session()

print(f"Session: {session_path}")
print(f"History: {len(messages) - 1} messages")
~~~

**步骤 4：替换三类消息写入**

用户消息原来使用：

~~~python
messages.append(
    {"role": "user", "content": user_message}
)
~~~

替换为：

~~~python
add_message(
    {"role": "user", "content": user_message}
)
~~~

模型消息：

~~~python
assistant_message = call_model(messages)
add_message(assistant_message)
~~~

Tool Result：

~~~python
add_message(
    {
        "role": "tool",
        "tool_call_id": tool_call["id"],
        "content": tool_result,
    }
)
~~~

**改造后的关键变化**

| 类型 | 位置 | 结果 |
| --- | --- | --- |
| 新增 | 配置之后 | 指定 Session JSONL |
| 新增 | 消息初始化之前 | 加载与追加 Session |
| 替换 | `messages` 初始化 | 启动时恢复历史 |
| 替换 | 三类 `append` | 同时保存到内存与磁盘 |

**运行与验收**

~~~bash
python learning-versions/07_v0.7_session/main.py
~~~

第一轮告诉模型“我叫小明”，输入 `/exit` 后重新运行，再询问名字。模型应能根据恢复的 Session 回答。

**完整代码入口：** [main.py](07_v0.7_session/main.py)

</details>

<details>
<summary><strong>📌 V0.8 — Context Compaction：如何控制不断增长的上下文？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    subgraph START["启动阶段"]
        A["启动程序"] --> B["加载模型配置"]
        B --> C["读取完整 Session JSONL"]
        C --> D["恢复 messages"]
        D --> E["复制为 context_messages（本版新增）"]
        E --> F["确定 Workspace"]
        F --> G["注册 Coding Tools 并生成 Schema"]
    end

    subgraph CHAT["Session 与 Context"]
        G --> H["读取用户输入"]
        H --> I{"输入是否为 /exit？"}
        I -- "是" --> J["程序结束，完整 Session 保留"]
        I -- "否" --> K["user 同时写入 Session 与 Context（本版修改）"]
    end

    subgraph COMPACT["Context Compaction（本版新增）"]
        K --> L{"Context 是否超过限制？"}
        L -- "否" --> Q["使用当前 Context"]
        L -- "是" --> M["切分旧消息与最近消息"]
        M --> N["单独调用 LLM 生成 Summary"]
        N --> O["System + Summary + Recent Messages"]
        O --> P["替换 context_messages"]
        P --> Q
    end

    subgraph AGENT["Agent Loop"]
        Q --> R["主模型读取精简 Context"]
        R --> S["assistant 同时写入 Session 与 Context"]
        S --> T{"是否有 Tool Call？"}
        T -- "否" --> U["输出 Final Answer"]
        U --> H
        T -- "是" --> V["Registry 查找并执行工具"]
        V --> W["得到结果或 Error"]
        W --> X["Tool Result 同时写入 Session 与 Context"]
        X --> L
    end
~~~

**上一版已经完成什么**

V0.7 会完整保存和恢复 Session，但每次模型调用仍把全部历史发送出去。

**引入问题**

Session 可以不断增长，模型 Context 却有长度和成本限制。直接发送全部历史，最终会超过窗口或显著增加请求成本。

**针对问题的解决方法**

将完整 `messages` 与实际发送的 `context_messages` 分离。Session 始终保存原始历史；Context 超限时，把旧消息总结成一条 Summary，只保留最近两轮原文。

**动手改造**

**步骤 1：修改 `add_message()`，同时更新两份消息**

原来的代码：

~~~python
def add_message(message):
    messages.append(message)
    # 写入 Session 文件
~~~

替换为：

~~~python
def add_message(message):
    messages.append(message)
    context_messages.append(message)

    session_path.parent.mkdir(parents=True, exist_ok=True)

    with session_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n")
~~~

**步骤 2：在加载 Session 后新增 Context 与教学阈值**

~~~python
messages = load_session()
context_messages = messages.copy()

MAX_CONTEXT_MESSAGES = 8
RECENT_TURNS = 2
~~~

**步骤 3：新增旧消息总结函数**

~~~python
def summarize_messages(old_messages):
    request_data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Summarize the earlier conversation concisely. "
                    "Preserve user facts, decisions, file changes, "
                    "tool results, and unfinished tasks."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    old_messages,
                    ensure_ascii=False,
                ),
            },
        ],
    }

    response = requests.post(
        url,
        headers=headers,
        json=request_data,
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]
~~~

摘要请求不发送 `tools`，因为这里的任务只是压缩文本。

**步骤 4：新增 `compact_context()`**

~~~python
def compact_context():
    global context_messages

    if len(context_messages) <= MAX_CONTEXT_MESSAGES:
        return

    user_indexes = [
        index
        for index, message in enumerate(context_messages)
        if message["role"] == "user"
    ]

    if len(user_indexes) <= RECENT_TURNS:
        return

    split_index = user_indexes[-RECENT_TURNS]
    old_messages = context_messages[1:split_index]
    recent_messages = context_messages[split_index:]
    summary = summarize_messages(old_messages)

    context_messages = [
        system_messages,
        {
            "role": "system",
            "content": f"Summary of earlier conversation:\n{summary}",
        },
        *recent_messages,
    ]
~~~

**步骤 5：让主模型只接收 Context**

把函数参数名和请求体中的消息来源从 `messages` 改为 `context`：

~~~python
def call_model(context):
    request_data = {
        "model": model,
        "messages": context,
        "tools": tools,
        "tool_choice": "auto",
    }
    # 发送请求并解析 assistant_message
    assistant_message.pop("reasoning", None)
    return assistant_message
~~~

**步骤 6：在 Agent Loop 每次调用模型前检查压缩**

原来的代码：

~~~python
assistant_message = call_model(messages)
~~~

替换为：

~~~python
compact_context()
assistant_message = call_model(context_messages)
~~~

**改造后的关键变化**

| 类型 | 位置 | 结果 |
| --- | --- | --- |
| 修改 | `add_message()` | 同时更新 Session 与 Context |
| 新增 | Session 加载之后 | 建立独立 Context 和压缩参数 |
| 新增 | 模型调用之前 | 总结旧消息并重组 Context |
| 修改 | `call_model()` | 只发送当前 Context |
| 修改 | Agent Loop | 每轮请求前执行压缩检查 |

**运行与验收**

~~~bash
python learning-versions/08_v0.8_context_compaction/main.py
~~~

连续提供名字、颜色、学习语言和目标等信息，第五轮再让模型复述。终端应出现：

~~~text
Context compacted: 6 messages → 1 summary
~~~

同时确认 JSONL 仍保留全部原始消息，Summary 没有覆盖 Session。

**完整代码入口：** [main.py](08_v0.8_context_compaction/main.py)

</details>

<details>
<summary><strong>📌 V0.9 — Skill：如何按需加载专业操作指南？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    subgraph START["启动阶段"]
        A["启动程序"] --> B["加载 .env 与运行配置"]
        B --> C["定位 SKILL.md（本版新增）"]
        C --> D["读取 Skill 元数据（本版新增）"]
        D --> E["把 Skill 名称、描述和读取方式写入 System Message（本版新增）"]
        E --> F["加载完整 Session"]
        F --> G["复制 Session，构造 Context"]
        G --> H["确定 Workspace"]
        H --> I["注册 read / write / edit / bash"]
        I --> J["由 Registry 生成 Tool Schema"]
    end

    subgraph SESSION["Session 与 Context"]
        K["读取用户输入"] --> L["user 消息写入完整 Session 与当前 Context"]
        L --> M{"Context 是否超过限制？"}
        M -- "否" --> P["使用当前 Context"]
        M -- "是" --> N["切分旧消息与最近消息"]
        N --> O["调用 LLM 生成 Summary"]
        O --> Q["System + Summary + Recent Messages"]
        Q --> P
    end

    subgraph LOOP["Agent Loop"]
        P --> R["调用 LLM"]
        R --> S["保存 assistant 消息到 Session 与 Context"]
        S --> T{"任务是否匹配 Skill？（本版新增）"}
        T -- "匹配，且尚未读取" --> U["模型生成 read Tool Call，读取完整 SKILL.md（本版新增）"]
        U --> V["Registry 查找 read"]
        V --> W["resolve_path 后读取 Skill 正文"]
        W --> X["Tool Result 写入 Session 与 Context"]
        X --> Y["LLM 根据 Skill 决定后续工具（本版新增）"]
        Y --> R
        T -- "不匹配或已经读取" --> Z{"是否存在 Tool Call？"}
        Z -- "否" --> AA["形成 Final Answer"]
        Z -- "是" --> AB["遍历 Tool Calls"]
    end

    subgraph TOOLS["Tool Runtime"]
        AB --> AC["Registry 按名称查找工具"]
        AC --> AD["执行 Coding Tool"]
        AD --> AE["形成成功结果或 Error Tool Result"]
        AE --> AF["Tool Result 写入完整 Session 与当前 Context"]
        AF --> M
    end

    subgraph OUTPUT["终端输出"]
        AA --> AG["终端输出回答"]
        AG --> K
    end

    J --> K
~~~

> 本版新增的是 Skill 的“先暴露元数据、匹配时再读取全文”链路。Session、Context 压缩、Agent Loop 和 Tool Result 回传仍然完整运行。

**上一版已经完成什么**

以 V0.8 为代码基线，我们已经拥有可恢复的 Session、可压缩的 Context、Coding Tools 和持续运行的 Agent Loop。

**引入问题**

模型会使用工具，但它并不知道项目特有的操作规范。例如，“做一次代码审查”可能要求固定的检查顺序和输出格式。如果把所有规范一直塞进 System Message，会让每次请求都携带大量无关文字。

实际现象是：

- 普通问答也要为很长的操作指南消耗 Context。
- 新增一类专业任务就要继续修改主提示词。
- 模型可能知道工具，却不知道团队希望它“怎样使用工具”。

**针对问题的解决方法**

把专业方法写进独立的 `SKILL.md`。程序启动时只读取很短的 `name` 和 `description`，让模型知道“有哪些 Skill”；任务匹配时，模型再通过现有 `read` 工具加载完整指南。

这是一种渐进披露：先告诉模型能力目录，需要时才加载细节。

**动手改造**

#### 第一步：新增 Skill 文件

**修改位置**：在 V0.9 目录下新建 `skills/code-review/SKILL.md`。

**新增代码：**

~~~markdown
---
name: code-review
description: Review code, explain its execution flow with a simple text flowchart, and report concise findings.
---

# Code Review

When reviewing code:

1. Read the target file.
2. Identify the main execution flow.
3. Check correctness and error handling.
4. Report findings clearly.

Always include:

1. A simple text flowchart using arrows.
2. A short findings list.
~~~

Front Matter 用于启动时发现 Skill，正文只在真正需要时读取。

#### 第二步：声明 Skill 路径

**修改位置**：`session_path` 与 `workspace` 等路径配置附近。

**新增代码：**

~~~python
skill_path = (
    Path(__file__).resolve().parent
    / "skills"
    / "code-review"
    / "SKILL.md"
)
~~~

#### 第三步：只解析 Skill 元数据

**修改位置**：`load_session()` 之后。

**新增代码：**

~~~python
def load_skill_metadata(path):
    metadata = {}

    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        if line == "---":
            break

        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata
~~~

这里没有把完整正文直接放进 Context，只提取第一段 `---` 之间的键值。

#### 第四步：把 Skill 目录写入 System Message

**修改位置**：原来的 `system_messages` 定义。

**原来的代码：**

~~~python
system_messages = {
    "role": "system",
    "content": (
        "You are a concise coding assistant. "
        "Answer ordinary conversation directly. "
        "Use tools only when the user explicitly asks you to operate on files or run commands. "
        "Session persistence is handled automatically by the runtime."
    ),
}
~~~

**替换为：**

~~~python
skill = load_skill_metadata(skill_path)

system_messages = {
    "role": "system",
    "content": (
        "You are a concise coding assistant. "
        "Answer ordinary conversation directly. "
        "Use tools only when the user explicitly asks you to operate on files or run commands. "
        "Session persistence is handled automatically by the runtime.\n\n"
        "Available skills:\n"
        f"- {skill['name']}: {skill['description']}\n"
        f"  Before using this skill, read {skill_path.as_posix()} with the read tool."
    ),
}
~~~

Agent Loop 不需要新增专用的 `run_skill()`。模型匹配到 Skill 后，会发出普通的 `read` Tool Call；读取结果作为 Tool Result 回到 Context，随后继续原有循环。

**改造后的关键变化**

- Skill 的简短元数据常驻 System Message，完整正文按需加载。
- Skill 复用现有 `read`、Registry 和 Agent Loop，没有建立第二套执行机制。
- Skill 正文的读取结果同时进入完整 Session 和当前 Context。
- Context 仍可压缩，磁盘中的 Session 仍保存完整历史。

**运行与验收**

~~~powershell
python learning-versions/09_v0.9_skill/main.py
~~~

建议依次输入：

1. `你好，请简单介绍自己`：应直接回答，不读取 Skill。
2. `请使用 code-review skill 审查 main.py`：应先调用 `read` 读取 `SKILL.md`，再读取目标文件。
3. 继续追问审查结果：Agent 应能利用 Context 中的 Skill 指南继续回答。

验收重点：普通任务不加载完整 Skill；匹配任务可以在同一 Agent Loop 中完成“读指南 → 读代码 → 给结论”。

**完整代码入口**

- [V0.9 完整 main.py](09_v0.9_skill/main.py)
- [code-review/SKILL.md](09_v0.9_skill/skills/code-review/SKILL.md)

</details>

<details>
<summary><strong>📌 V0.10 — Extension：如何在不修改主循环的情况下增加工具？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    subgraph START["启动阶段"]
        A["启动程序"] --> B["加载配置"]
        B --> C["读取 Skill 元数据并写入 System Message"]
        C --> D["扫描 extensions/*.py（本版新增）"]
        D --> E["动态导入 Extension 模块（本版新增）"]
        E --> F["调用 module.setup(pi)（本版新增）"]
        F --> G["ExtensionAPI.register_tool（本版新增）"]
        G --> H["Extension Tool 进入完整 Registry（本版新增）"]
        H --> I["注册核心 Coding Tools"]
        I --> J["从完整 Registry 生成 Tool Schema（本版修改）"]
        J --> K["加载完整 Session"]
        K --> L["复制 Session，构造 Context"]
    end

    subgraph SESSION["Session 与 Context"]
        M["读取用户输入"] --> N["user 消息写入完整 Session 与当前 Context"]
        N --> O{"Context 是否超过限制？"}
        O -- "是" --> P["旧消息交给 LLM 生成 Summary"]
        P --> Q["System + Summary + Recent Messages"]
        O -- "否" --> R["保留当前 Context"]
        Q --> R
    end

    subgraph LOOP["Agent Loop"]
        R --> S["调用 LLM"]
        S --> T["保存 assistant 消息"]
        T --> U{"Skill 是否匹配且需要加载？"}
        U -- "是" --> V["生成 read Tool Call，读取完整 SKILL.md"]
        V --> Z
        U -- "否或已加载" --> X{"是否存在 Tool Call？"}
        X -- "否" --> Y["形成 Final Answer"]
        X -- "是" --> Z["遍历 Tool Calls"]
    end

    subgraph TOOLS["Tool Runtime"]
        Z --> AA["Registry 按名称查找"]
        AA --> AB{"核心工具还是 Extension Tool？（本版新增）"}
        AB -- "核心工具" --> AC["执行 read / write / edit / bash"]
        AB -- "Extension Tool" --> AD["执行扩展注册的 execute（本版新增）"]
        AC --> AE["形成 Tool Result"]
        AD --> AE
        AE --> AF["Tool Result 写入完整 Session 与当前 Context"]
        AF --> O
    end

    subgraph OUTPUT["终端输出"]
        Y --> AG["终端输出回答"]
        AG --> M
    end

    L --> M
~~~

> Extension 只改变启动时的工具注册方式。运行阶段仍是同一条 Session → Context → Agent Loop → Registry → Tool Result 链路。

**上一版已经完成什么**

V0.9 已让模型按需读取 Skill，并保留 Session、Compaction、Registry 和 Coding Tools。

**引入问题**

新增工具仍需要直接编辑 `main.py`：写函数、修改 `tool_registry`、重新生成 Schema。工具越来越多时，主程序会不断膨胀，第三方能力也很难独立分发。

实际现象是：即使只是增加一个“统计单词数”的小工具，也必须侵入主循环所在文件。

**针对问题的解决方法**

约定 Extension 模块公开一个 `setup(pi)` 函数。主程序启动时扫描 `extensions` 目录，把最小 API 对象传进去；Extension 通过 `pi.register_tool(...)` 把工具注册到同一个 Registry。

注册完成后，Schema 仍由 Registry 统一生成，Agent Loop 也仍按名称查找工具，因此运行阶段无需区分工具来自主程序还是扩展。

**动手改造**

#### 第一步：引入动态导入模块并声明扩展目录

**修改位置**：文件顶部 import 区域和路径配置区域。

**新增代码：**

~~~python
import importlib.util

extension_dir = (
    Path(__file__).resolve().parent
    / "extensions"
)
~~~

#### 第二步：编写第一个 Extension

**修改位置**：新建 `extensions/word_count.py`。

**新增代码：**

~~~python
def word_count(text):
    return f"Word count: {len(text.split())}"


def setup(pi):
    pi.register_tool(
        name="word_count",
        description="Count the number of words in the given text.",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to count words in."
                }
            },
            "required": ["text"]
        },
        execute=word_count,
    )
~~~

Extension 不需要导入 `main.py`，也不直接接触 Session 或 Agent Loop。

#### 第三步：给 Extension 一个最小注册 API

**修改位置**：`tool_registry` 定义之后、生成 `tools` 之前。

**新增代码：**

~~~python
class ExtensionAPI:
    def register_tool(self, name, description, parameters, execute):
        tool_registry[name] = {
            "description": description,
            "parameters": parameters,
            "execute": execute,
        }
~~~

#### 第四步：扫描并加载扩展

**修改位置**：`ExtensionAPI` 之后。

**新增代码：**

~~~python
def load_extensions():
    pi = ExtensionAPI()

    for path in sorted(extension_dir.glob("*.py")):
        spec = importlib.util.spec_from_file_location(
            f"extension_{path.stem}",
            path,
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        module.setup(pi)
        print(f"Extension loaded: {path.stem}")
~~~

#### 第五步：先加载 Extension，再生成 Tool Schema

**修改位置**：原来的 `tools = [...]` 之前。

**原来的代码：**

~~~python
tools = [
    {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }
    for tool_name, tool in tool_registry.items()
]
~~~

**替换为：**

~~~python
load_extensions()

tools = [
    {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }
    for tool_name, tool in tool_registry.items()
]
~~~

顺序很重要：如果先生成 `tools`，后注册的 `word_count` 不会出现在发给模型的 Tool Schema 中。

**改造后的关键变化**

- 核心工具与 Extension Tool 汇入同一个 Registry。
- Extension 只依赖小型 `ExtensionAPI`，不用理解主循环内部实现。
- 工具 Schema 在所有扩展加载完成后统一生成。
- Skill、Session、Context 压缩和 Agent Loop 的行为保持不变。

**运行与验收**

~~~powershell
python learning-versions/10_v0.10_extension/main.py
~~~

输入 `请使用 word_count 统计：Agents learn by doing`。

应先看到 `Extension loaded: word_count`，随后模型生成 `word_count` Tool Call，扩展返回计数结果，结果写回 Session 与 Context，模型再形成最终回答。

**完整代码入口**

- [V0.10 完整 main.py](10_v0.10_extension/main.py)
- [word_count Extension](10_v0.10_extension/extensions/word_count.py)

</details>

<details>
<summary><strong>📌 V0.11 — Event：如何让运行时与终端展示解耦？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    subgraph START["启动阶段"]
        A["启动程序"] --> B["注册 Renderer Observer（本版新增）"]
        B --> C["加载配置与 Skill 元数据"]
        C --> D["扫描并加载 Extensions"]
        D --> E["核心工具与 Extension Tool 进入 Registry"]
        E --> F["由完整 Registry 生成 Tool Schema"]
        F --> G["加载完整 Session"]
        G --> H["复制 Session，构造 Context"]
    end

    subgraph SESSION["Session 与 Context"]
        I["读取用户输入"] --> J["user 消息写入完整 Session 与当前 Context"]
        J --> K{"Context 是否超过限制？"}
        K -- "是" --> L["旧消息交给 LLM 生成 Summary"]
        L --> M["System + Summary + Recent Messages"]
        K -- "否" --> N["保留当前 Context"]
        M --> N
    end

    subgraph LOOP["Agent Loop"]
        N --> O["调用 LLM"]
        O --> P["保存 assistant 消息到 Session 与 Context"]
        P --> Q{"Skill 是否匹配且需要加载？"}
        Q -- "是" --> R["生成 read Tool Call，读取完整 SKILL.md"]
        R --> V
        Q -- "否或已加载" --> T{"是否存在 Tool Call？"}
        T -- "否" --> U["emit agent_end（本版修改）"]
        T -- "是" --> V["遍历 Tool Calls"]
    end

    subgraph TOOLS["Tool Runtime"]
        V --> W["emit tool_start（本版新增）"]
        AE --> X["Registry 查找核心工具或 Extension Tool"]
        X --> Y["执行工具"]
        Y --> Z["形成成功结果或 Error Tool Result"]
        Z --> AA["emit tool_end（本版新增）"]
        AH --> AB["Tool Result 写入完整 Session 与当前 Context"]
        AB --> K
    end

    subgraph EVENTS["Event 与终端输出（本版新增）"]
        W --> AC["Event Observer 接收 tool_start"]
        AC --> AD["Renderer 格式化工具开始事件"]
        AD --> AE["Terminal 展示工具名称与参数"]
        AA --> AF["Event Observer 接收 tool_end"]
        AF --> AG["Renderer 格式化工具结果事件"]
        AG --> AH["Terminal 展示 Tool Result"]
        U --> AI["Event Observer 接收 agent_end"]
        AI --> AJ["Renderer 格式化最终回答"]
        AJ --> AK["Terminal 输出回答"]
    end

    AK --> I
    H --> I
~~~

> 本版没有改变模型和工具怎样协作，而是在完整运行链路旁增加 Event → Observer → Renderer → Terminal 的输出通道。

**上一版已经完成什么**

V0.10 已拥有 Skill、Extension、Session、Context Compaction、Agent Loop 和统一 Tool Registry。运行逻辑完整，但主循环仍直接负责打印各种结果。

**引入问题**

`main.py` 里散落着普通回答、工具调用和工具结果的 `print()`。如果以后同时输出到终端、日志文件或网页，就要在每个业务分支重复修改展示代码。

实际现象是：Runtime 负责“发生了什么”，却同时决定“应该怎样显示”，两种职责耦合在一起。

**针对问题的解决方法**

Runtime 不再直接打印关键运行节点，而是发出结构化 Event：

- `agent_end`：Agent 已形成最终答案。
- `tool_start`：即将执行某个工具。
- `tool_end`：工具执行完成。

Observer 接收 Event，`renderer.py` 决定如何展示。以后增加日志或 Web UI，只需新增 Observer，不必改写 Agent Loop。

**动手改造**

#### 第一步：新增终端 Renderer

**修改位置**：在 V0.11 目录新建 `renderer.py`。

**新增代码：**

~~~python
def render_event(event):
    event_type = event["type"]

    if event_type == "model_start":
        print("Answer: ", end="", flush=True)

    elif event_type == "model_delta":
        print(event["delta"], end="", flush=True)

    elif event_type == "model_end":
        print()

    elif event_type == "tool_start":
        print(
            f"调用工具 Tool Call: {event['name']}, "
            f"参数: {event['arguments']}"
        )
    elif event_type == "tool_end":
        print(
            "工具执行结果 Tool Result:\n"
            f"{event['result']}"
        )
    elif event_type == "agent_end":
        print(f"Answer: {event['answer']}")
~~~

#### 第二步：注册 Observer 并提供统一事件入口

**修改位置**：`main.py` import 区域以及配置初始化之后。

**新增代码：**

~~~python
from renderer import render_event

event_handlers = [render_event]


def emit(event_type, **data):
    event = {
        "type": event_type,
        **data,
    }

    for handler in event_handlers:
        handler(event)
~~~

`emit()` 只描述事件，不包含终端格式；每个 Handler 自己决定如何消费。

#### 第三步：最终回答改为发送 agent_end

**修改位置**：Agent Loop 中 `if not tool_calls:` 分支。

**原来的代码：**

~~~python
if not tool_calls:
    print(f"Answer: {assistant_message['content']}")
    break
~~~

**替换为：**

~~~python
if not tool_calls:
    emit(
        "agent_end",
        answer=assistant_message["content"],
    )
    break
~~~

#### 第四步：工具执行前发送 tool_start

**修改位置**：Registry 找到 `tool` 之后、真正执行之前。

**原来的代码：**

~~~python
print(
    f"调用工具 Tool Call: {tool_name}, "
    f"参数: {tool_arguments}"
)
~~~

**替换为：**

~~~python
emit(
    "tool_start",
    name=tool_name,
    arguments=tool_arguments,
)
~~~

#### 第五步：工具执行后发送 tool_end

**修改位置**：得到 `tool_result` 之后、调用 `add_message()` 之前。

**原来的代码：**

~~~python
print(f"工具执行结果 Tool Result:\n{tool_result}")
~~~

**替换为：**

~~~python
emit(
    "tool_end",
    result=tool_result,
)
~~~

注意：Event 只负责观察和展示。`add_message()` 仍必须执行，Tool Result 才会进入完整 Session 与当前 Context，并回到下一轮模型调用。

**改造后的关键变化**

- Agent Loop 只报告 `agent_end`、`tool_start`、`tool_end` 等事实。
- Renderer 统一管理终端文案和格式。
- Event 展示链路不会取代 Session 持久化或 Tool Result 回传。
- Skill 和 Extension 的调用仍通过同一套 Registry 与 Agent Loop。

**运行与验收**

~~~powershell
python learning-versions/11_v0.11_event_and_streaming/main.py
~~~

输入 `请读取 README.md，并告诉我第一行是什么`。

终端应按顺序显示工具开始、工具结果和最终回答；`sessions` 中则仍应保存 user、assistant 和 tool 消息。删除或替换 Renderer 不应影响工具真正执行。

**完整代码入口**

- [V0.11 完整 main.py](11_v0.11_event_and_streaming/main.py)
- [V0.11 renderer.py](11_v0.11_event_and_streaming/renderer.py)

</details>

<details>
<summary><strong>📌 V0.12 — Sandbox：如何在真实执行前拦截高风险工具？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    subgraph START["启动阶段"]
        A["启动程序"] --> B["注册 Renderer Observer"]
        B --> C["加载配置"]
        C --> D["读取 Skill 元数据并写入 System Message"]
        D --> E["扫描 Extensions"]
        E --> F["Extension 通过 setup(pi) 注册 Tool"]
        F --> G["核心工具与 Extension Tool 组成完整 Registry"]
        G --> H["创建 Sandbox 工具白名单（本版新增）"]
        H --> I["由完整 Registry 生成 Tool Schema"]
        I --> J["加载完整 Session"]
        J --> K["复制 Session，构造 Context"]
    end

    subgraph SESSION["Session 与 Context"]
        L["读取用户输入"] --> M["user 消息写入完整 Session 与当前 Context"]
        M --> N{"Context 是否超过限制？"}
        N -- "是" --> O["切分旧消息与最近消息"]
        O --> P["调用 LLM 生成 Summary"]
        P --> Q["System + Summary + Recent Messages"]
        N -- "否" --> R["保留当前 Context"]
        Q --> R
    end

    subgraph LOOP["Agent Loop"]
        R --> S["调用 LLM"]
        S --> T["保存 assistant 消息到完整 Session 与当前 Context"]
        T --> U{"Skill 是否匹配且需要加载？"}
        U -- "是" --> V["生成 read Tool Call，按需读取完整 SKILL.md"]
        V --> Z
        U -- "否或已加载" --> X{"是否存在 Tool Call？"}
        X -- "否" --> Y["emit agent_end"]
        X -- "是" --> Z["遍历 Tool Calls"]
    end

    subgraph TOOLS["Tool Runtime"]
        Z --> AA["emit tool_start"]
        AL --> AB["Registry 查找核心工具或 Extension Tool"]
        AB --> AC["Sandbox.check(tool_name)（本版新增）"]
        AC --> AD{"白名单是否允许？（本版新增）"}
        AD -- "允许" --> AE["真实执行工具"]
        AD -- "拒绝" --> AF["生成 PermissionError，不执行工具"]
        AE --> AG["形成 Tool Result"]
        AF --> AG
        AG --> AH["emit tool_end"]
        AO --> AI["Tool Result 写入完整 Session 与当前 Context"]
        AI --> N
    end

    subgraph EVENTS["Event 与终端输出"]
        AA --> AJ["Event Observer 接收 tool_start"]
        AJ --> AK["Renderer 格式化工具开始事件"]
        AK --> AL["Terminal 展示工具名称与参数"]
        AH --> AM["Event Observer 接收 tool_end"]
        AM --> AN["Renderer 格式化工具结果事件"]
        AN --> AO["Terminal 展示 Tool Result"]
        Y --> AP["Event Observer 接收 agent_end"]
        AP --> AQ["Renderer 格式化最终回答"]
        AQ --> AR["Terminal 输出回答"]
    end

    AR --> L
    K --> L
~~~

> 完整链路中，Skill 在启动时只暴露元数据、匹配时按需加载；Extension 在启动时注册工具；Session 保存完整消息；Context 可以压缩；Event 负责展示；Sandbox 位于 Registry 查找之后、真实工具执行之前。

**上一版已经完成什么**

V0.11 已把完整运行时事件交给 Renderer 展示，同时保留 Skill、Extension、Session、Context、Agent Loop 和 Tool Registry。

**引入问题**

模型看见 Tool Schema 后，可以选择 Registry 中的任何工具。`bash` 很有用，但也可能删除文件或执行超出教程预期的命令。仅靠提示词要求模型“小心”并不是可靠的执行边界。

实际现象是：Registry 负责找到工具，却没有在真实执行前进行强制权限判断。

**针对问题的解决方法**

增加一个最小 Sandbox 白名单。Registry 仍负责“这个工具是否存在”，Sandbox 接着判断“这个工具是否允许执行”：

- 允许：调用真实 `execute`。
- 拒绝：抛出 `PermissionError`，由原有异常处理转成 Error Tool Result。

这样模型会看到拒绝结果并继续 Agent Loop，但高风险函数本身没有运行。

**动手改造**

#### 第一步：实现 Sandbox

**修改位置**：在 V0.12 目录新建 `sandbox.py`。

**新增代码：**

~~~python
class Sandbox:
    def __init__(self, allowed_tools):
        self.allowed_tools = allowed_tools

    def check(self, tool_name):
        if tool_name not in self.allowed_tools:
            raise PermissionError(
                f"Sandbox blocked tool: {tool_name}"
            )
~~~

#### 第二步：导入 Sandbox

**修改位置**：`main.py` import 区域，紧邻 Renderer import。

**新增代码：**

~~~python
from renderer import render_event
from sandbox import Sandbox
~~~

#### 第三步：创建工具白名单

**修改位置**：`load_extensions()` 之后、生成 `tools` Schema 之前。

**新增代码：**

~~~python
sandbox = Sandbox(
    allowed_tools={"read", "write", "edit", "word_count"}
)
~~~

`bash` 仍保留在 Registry 和 Tool Schema 中，方便观察“模型请求了工具，但 Runtime 拒绝执行”的完整路径。

#### 第四步：在真实执行前检查权限

**修改位置**：Agent Loop 内已经取得 `tool`、已经发送 `tool_start`，准备执行 `tool["execute"]` 的位置。

**原来的代码：**

~~~python
try:
    tool_result = tool["execute"](**tool_arguments)
except Exception as e:
    tool_result = f"Error: {e}"
~~~

**替换为：**

~~~python
try:
    sandbox.check(tool_name)
    tool_result = tool["execute"](**tool_arguments)
except Exception as e:
    tool_result = f"Error: {e}"
~~~

检查必须位于 Registry 查询之后、`execute` 之前。拒绝信息沿用 Tool Result 回传路径，因此 Event、Session、Context 和 Agent Loop 都不需要新分支代码。

#### 第五步：只用虚构文件准备删除实验

**修改位置**：无需修改 Python 代码，在 V0.12 的 `test` 目录准备测试数据。

~~~powershell
python learning-versions/12_v0.12_sandbox/main.py
~~~

测试时只允许操作仓库中专门准备的虚构文件：

- `test/protected/private_config.txt`：模拟受保护配置。
- `test/backup/private_config.backup.txt`：恢复用备份。

建议请求：`请用 bash 删除 test/protected/private_config.txt`。终端应通过 Event 显示 `Sandbox blocked tool: bash`，文件仍然存在。

#### 第六步：对照理解 Sandbox 的边界

若要做“无 Sandbox”对照实验，也只能在 V0.12 的虚构 `test` 目录中进行。先确认备份存在，再临时将 `bash` 加入白名单；实验后立即恢复代码和测试文件：

~~~powershell
Copy-Item learning-versions\12_v0.12_sandbox\test\backup\private_config.backup.txt learning-versions\12_v0.12_sandbox\test\protected\private_config.txt -Force
~~~

> ⚠️ 不要把真实配置、个人文件或项目源码作为删除实验目标。Sandbox 只是教学版的工具名白名单，不是操作系统级隔离。

**改造后的关键变化**

- Registry 决定“调用哪个工具”，Sandbox 决定“是否允许真实执行”。
- 被拒绝的工具不会执行，其 `PermissionError` 会转换成 Tool Result。
- Tool Result 仍会经过 Event 展示，并写入完整 Session 与当前 Context。
- Sandbox 没有替代路径限制：`read`、`write`、`edit` 仍继续经过 `resolve_path()`。
- Skill 与 Extension 的发现、加载和执行链路保持完整。

**运行与验收**

~~~powershell
python learning-versions/12_v0.12_sandbox/main.py
~~~

建议按顺序验收：

1. 请求 `read` 读取虚构文件：白名单允许，应正常返回。
2. 请求 `word_count`：Extension Tool 在白名单内，应正常执行。
3. 请求 `bash` 删除虚构文件：应返回 `Error: Sandbox blocked tool: bash`。
4. 检查 `test/protected/private_config.txt`：文件应仍存在。
5. 检查 Session：应保存模型的 Tool Call 和 Sandbox 拒绝产生的 Tool Result。

**完整代码入口**

- [V0.12 完整 main.py](12_v0.12_sandbox/main.py)
- [V0.12 sandbox.py](12_v0.12_sandbox/sandbox.py)
- [V0.12 renderer.py](12_v0.12_sandbox/renderer.py)
- [虚构受保护文件](12_v0.12_sandbox/test/protected/private_config.txt)
- [恢复用备份](12_v0.12_sandbox/test/backup/private_config.backup.txt)

</details>

<details>
<summary><strong>📌 V0.13 — SubAgent：一个 Agent 不够时如何安全委托？</strong></summary>

**完整系统运转流程**

~~~mermaid
flowchart TD
    subgraph START["启动阶段"]
        A["启动程序"] --> B["注册 Renderer Observer"]
        B --> C["加载配置与 Skill 元数据"]
        C --> D["扫描 Extensions 并注册 Extension Tool"]
        D --> E["注册核心工具和两个委托工具（本版新增）"]
        E --> F["创建包含委托工具的 Sandbox 白名单（本版修改）"]
        F --> G["由完整 Registry 生成 Parent Tool Schema"]
        G --> H["加载 Parent 完整 Session（本版修改）"]
        H --> I["复制 Parent Session，构造 Parent Context"]
    end

    subgraph PCTX["Parent Session 与 Context"]
        J["读取用户输入"] --> K["user 写入 Parent Session 与 Parent Context"]
        K --> L{"Parent Context 是否超过限制？"}
        L -- "是" --> M["旧消息交给 LLM 生成 Summary"]
        M --> N["System + Summary + Recent Messages"]
        L -- "否" --> O["保留当前 Parent Context"]
        N --> O
    end

    subgraph PLOOP["Parent Agent Loop"]
        O --> P["调用 Parent LLM"]
        P --> Q["assistant 写入 Parent Session 与 Parent Context"]
        Q --> R{"Skill 是否匹配且需要加载？"}
        R -- "是" --> S["生成 read Tool Call，按需读取完整 SKILL.md"]
        S --> U
        R -- "否或已加载" --> T{"是否存在 Tool Call？"}
        T -- "否" --> V["emit agent_end"]
        T -- "是" --> U["遍历 Parent Tool Calls"]
    end

    subgraph TOOL["Parent Tool Runtime"]
        U --> W["emit tool_start"]
        Z --> AA["Registry 查找核心、Extension 或委托工具"]
        AA --> AB["Sandbox.check(tool_name)"]
        AB --> AC{"白名单是否允许？"}
        AC -- "拒绝" --> AD["生成 PermissionError，不执行工具"]
        AC -- "允许" --> AE{"是否为委托工具？（本版新增）"}
        AE -- "否" --> AF["执行核心工具或 Extension Tool"]
        AE -- "是" --> AG["delegate_explorer / delegate_comparator（本版新增）"]
    end

    subgraph CHILD["SubAgent / Child Agent Loop（本版新增）"]
        AG --> AH["选择 Explorer 或 Comparator 的职责提示词"]
        AH --> AI["创建独立 Child Messages"]
        AI --> AJ["user 写入对应 Child Session JSONL"]
        AJ --> AK["调用 LLM，只传 read Tool Schema"]
        AK --> AL["assistant 写入 Child Messages 与 Child Session"]
        AL --> AM{"Child 是否存在 Tool Call？"}
        AM -- "否" --> AN["返回 Child Final Result"]
        AM -- "是" --> AO{"工具是否为 read？"}
        AO -- "否" --> AP["生成 Child 工具拒绝结果"]
        AO -- "是" --> AQ["resolve_path 后读取项目文件"]
        AP --> AR["Tool Result 写入 Child Messages 与 Child Session"]
        AQ --> AR
        AR --> AK
    end

    subgraph RESULT["结果回传"]
        AF --> AS["形成普通 Tool Result"]
        AD --> AS
        AN --> AT["Child Final Result 成为委托工具结果（本版新增）"]
        AS --> AU["emit tool_end"]
        AT --> AU
        AX --> AY["Tool Result 写入 Parent Session 与 Parent Context"]
        AY --> L
    end

    subgraph EVENT["Event 与终端输出"]
        W --> AW["Observer → Renderer → Terminal 展示工具开始"]
        AW --> Z["继续 Parent Tool Runtime"]
        AU --> AX["Observer → Renderer → Terminal 展示工具结果"]
        V --> AZ["Observer → Renderer → Terminal 输出 Parent 最终回答"]
    end

    AZ --> BA["等待下一轮用户输入"]
    BA --> J
    I --> J
~~~

> V0.13 没有建立一条脱离主系统的“第二套 Agent”。Parent 把委托看成普通 Tool Call；Child 在独立 Messages 和 Session 中运行受限 Agent Loop，最终结果再作为 Tool Result 回到 Parent。

**上一版已经完成什么**

V0.12 已具备 Skill、Extension、Session、Context Compaction、Agent Loop、Event、Renderer、统一 Tool Registry 和 Sandbox。单个 Agent 已能安全地使用允许的工具完成任务。

**引入问题**

复杂任务经常同时包含不同类型的工作。例如，解释代码时既要梳理执行流程，又要比较两个版本的差异。让一个 Agent 在同一 Context 中承担所有角色，会出现三个问题：

- 职责混在一起，输出格式容易互相干扰。
- 中间阅读结果全部进入 Parent Context，消息增长更快。
- 无法针对子任务单独限制工具和保存执行记录。

**针对问题的解决方法**

把专业子任务包装成两个委托工具：

- `delegate_explorer`：启动 Explorer Child，读取文件并返回箭头流程图。
- `delegate_comparator`：启动 Comparator Child，读取文件并返回 Markdown 对比表。

Parent 仍通过 Tool Call 自主决定是否委托。每个 Child 使用独立的 System Message、Messages 和 JSONL Session，并且只接收 `read` Tool Schema。Child 的 Final Result 返回后，沿用普通 Tool Result 链路进入 Parent Context。

**动手改造**

**步骤 1：引入 SubAgent Runtime，并拆分三份 Session**

**修改位置**：`main.py` 的 import 区域和原 `session_path` 定义。

**新增代码：**

~~~python
from subagent import run_subagent
~~~

**原来的代码：**

~~~python
session_path = Path("sessions/session-008.jsonl")
~~~

**替换为：**

~~~python
session_path = Path("sessions/session-011-parent.jsonl")
explorer_session_path = Path("sessions/session-011-explorer.jsonl")
comparator_session_path = Path("sessions/session-011-comparator.jsonl")
~~~

Parent 继续由原来的 `load_session()` 和 `add_message()` 管理；两个 Child 的消息由 `subagent.py` 写入各自文件。

**步骤 2：告诉 Parent 何时委托，并定义两个 Child 的职责**

**修改位置**：原来的 `system_messages`，以及它后方的提示词配置。

**原来的代码：**

~~~python
system_messages = {
    "role": "system",
    "content": (
        "You are a concise coding assistant. "
        "Answer ordinary conversation directly. "
        "Use tools only when the user explicitly asks you to operate on files or run commands. "
        "Session persistence is handled automatically by the runtime.\n\n"
        "Available skills: \n"
        f"- {skill['name']}: {skill['description']}\n"
        f"  Before using this skill, read {skill_path.as_posix()} with the read tool."
    ),
}
~~~

**替换为：**

~~~python
system_messages = {
    "role": "system",
    "content": (
        "You are a concise coding assistant. "
        "Answer ordinary conversation directly. "
        "Use tools only when the user explicitly asks you to operate on files or run commands. "
        "Use delegate_explorer to create execution flowcharts. "
        "Use delegate_comparator to create comparison tables. "
        "Use the appropriate subagents and combine their results. "
        "Session persistence is handled automatically by the runtime.\n\n"
        "Available skills: \n"
        f"- {skill['name']}: {skill['description']}\n"
        f"  Before using this skill, read {skill_path.as_posix()} with the read tool."
    ),
}

EXPLORER_PROMPT = (
    "You are a flowchart subagent. "
    "Read relevant files and return a concise text flowchart using arrows."
)

COMPARATOR_PROMPT = (
    "You are a comparison subagent. "
    "Compare relevant files and return a concise Markdown table."
)
~~~

Parent 的提示词只说明委托策略；Child 的提示词只保留自己的专业职责。

**步骤 3：新增独立的 Child Agent Loop**

**修改位置**：新建 `subagent.py`。

**新增代码：**

~~~python
import json


def add_message(messages, session_path, message):
    messages.append(message)

    session_path.parent.mkdir(parents=True, exist_ok=True)

    with open(session_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n")


def run_subagent(
    task,
    system_message,
    call_model,
    read_file,
    tools,
    session_path,
):
    messages = [
        {
            "role": "system",
            "content": system_message,
        },
    ]

    add_message(
        messages,
        session_path,
        {
            "role": "user",
            "content": task,
        },
    )

    while True:
        assistant_message = call_model(messages, tools)
        add_message(messages, session_path, assistant_message)

        tool_calls = assistant_message.get("tool_calls")

        if not tool_calls:
            return assistant_message["content"]

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_arguments = json.loads(
                tool_call["function"]["arguments"]
            )

            if tool_name != "read":
                tool_result = (
                    f"Error: Subagent cannot use tool: {tool_name} "
                )
            else:
                try:
                    tool_result = read_file(**tool_arguments)
                except Exception as e:
                    tool_result = f"Error: {e}"

            add_message(
                messages,
                session_path,
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result,
                },
            )
~~~

这里的 `messages` 是每次委托新建的 Child Context；`session_path` 则让 Explorer 和 Comparator 的执行记录分别落盘。

**步骤 4：让 Parent 和 Child 可以使用不同 Tool Schema**

**修改位置**：`call_model()` 的函数签名和请求体。

**原来的代码：**

~~~python
def call_model(context):
    request_data = {
        "model": model,
        "messages": context,
        "tools": tools,
        "tool_choice": "auto",
    }
~~~

**替换为：**

~~~python
def call_model(context, available_tools=None):
    if available_tools is None:
        available_tools = tools

    request_data = {
        "model": model,
        "messages": context,
        "tools": available_tools,
        "tool_choice": "auto",
    }
~~~

Parent 不传第二个参数，因此看到完整工具集；Child 显式传入筛选后的只读工具列表。

**步骤 5：构造两个委托入口**

**修改位置**：Coding Tool 函数之后、`tool_registry` 之前。

**新增代码：**

~~~python
def delegate_task(task, system_message, child_session_path):
    subagent_tools = [
        tool
        for tool in tools
        if tool["function"]["name"] == "read"
    ]

    return run_subagent(
        task,
        system_message,
        call_model,
        read_file,
        subagent_tools,
        child_session_path,
    )


def delegate_explorer(task):
    return delegate_task(
        task,
        EXPLORER_PROMPT,
        explorer_session_path,
    )


def delegate_comparator(task):
    return delegate_task(
        task,
        COMPARATOR_PROMPT,
        comparator_session_path,
    )
~~~

`delegate_task()` 复用同一个 Child Runtime，但通过职责提示词和 Session 路径隔离两个角色。

**步骤 6：把委托能力注册为普通工具**

**修改位置**：`tool_registry` 字典中，紧跟现有 Coding Tools。

**新增代码：**

~~~python
"delegate_explorer": {
    "description": "Create a text flowchart that explains a file's execution flow.",
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The exploration task.",
            }
        },
        "required": ["task"],
    },
    "execute": delegate_explorer,
},

"delegate_comparator": {
    "description": "Compare files or versions and return a concise Markdown table.",
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The comparison task for the SubAgent.",
            }
        },
        "required": ["task"],
    },
    "execute": delegate_comparator,
},
~~~

注册后，Parent 可以像选择 `read` 或 `word_count` 一样，由模型自主选择委托工具。

**步骤 7：允许 Parent 启动两个 Child**

**修改位置**：原来的 Sandbox 白名单。

**原来的代码：**

~~~python
sandbox = Sandbox(
    allowed_tools={"read", "write", "edit", "word_count"}
)
~~~

**替换为：**

~~~python
sandbox = Sandbox(
    allowed_tools={
        "read",
        "write",
        "edit",
        "word_count",
        "delegate_explorer",
        "delegate_comparator",
    }
)
~~~

Sandbox 只允许 Parent 启动已登记的委托。Child 内部仍在 `run_subagent()` 中强制只接受 `read`。

**改造后的关键变化**

- Parent 可以根据任务自主选择 Explorer、Comparator 或普通工具。
- Explorer 与 Comparator 拥有不同职责提示词、独立 Messages 和独立 JSONL Session。
- Child 只看到 `read` Tool Schema，代码还会再次拒绝任何非 `read` Tool Call。
- Child Final Result 作为普通 Tool Result 返回 Parent，因此 Parent Agent Loop、Event、Renderer 和 Context Compaction 都可以继续复用。
- 两个 Child 当前按 Parent Tool Call 的顺序执行；V0.13 尚未引入并行调度。

**运行与验收**

~~~powershell
python learning-versions/13_v0.13_subagent/main.py
~~~

建议输入：

~~~text
请让 Explorer 分析 learning-versions/01_v0.1_first_llm_call/main.py 的执行流程，
再让 Comparator 对比 V0.1 和 V0.2 的差异，最后汇总两个结果。
~~~

验收时观察：

1. Parent 自主生成 `delegate_explorer` 和 `delegate_comparator` Tool Call。
2. Explorer 读取 V0.1，并返回箭头流程图。
3. Comparator 读取 V0.1、V0.2，并返回 Markdown 对比表。
4. Parent 收到两个 Child Result 后组合最终回答。
5. `sessions/session-011-parent.jsonl`、`session-011-explorer.jsonl` 和 `session-011-comparator.jsonl` 分别保存各自消息。
6. Child Session 中只出现 `read` Tool Call；两个 Child 当前顺序执行。

**完整代码入口**

- [V0.13 完整 main.py](13_v0.13_subagent/main.py)
- [V0.13 subagent.py](13_v0.13_subagent/subagent.py)
- [V0.13 sandbox.py](13_v0.13_subagent/sandbox.py)
- [V0.13 renderer.py](13_v0.13_subagent/renderer.py)
- [word_count Extension](13_v0.13_subagent/extensions/word_count.py)
- [code-review Skill](13_v0.13_subagent/skills/code-review/SKILL.md)

</details>

## 后续路线图

| 版本 | 主题 | 状态 |
|---|---|---|
| V0.14 | Durable Run | 计划中 |
| V1.0 | Micro Pi Core | 计划中 |

> 路线图只说明方向。对应版本完成并验收后，再补充完整系统流程和渐进式教程。
