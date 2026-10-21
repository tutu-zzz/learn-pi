import os

import json
import requests
import subprocess
import importlib.util

from dotenv import load_dotenv
from pathlib import Path

# [V0.11 新增] 终端事件渲染器
from renderer import render_event
# [V0.12 新增] 工具权限检查
from sandbox import Sandbox
# [V0.13 新增] Subagent Runtime
from subagent import run_subagent
# [V0.14 新增] Durable Run Checkpoint
from durable import load_checkpoint, save_checkpoint


# 加载配置
load_dotenv()

base_url = os.getenv("MICRO_PI_BASE_URL")
model = os.getenv("MICRO_PI_MODEL")
api_key = os.getenv("MICRO_PI_API_KEY")

if not base_url or not model or not api_key:
    raise RuntimeError("模型配置不完整")

print(f"Base URL: {base_url}")
print(f"Model: {model}")


'''
https://api.openai.com/v1  +  /chat/completions
        ↑ 服务地址              ↑ 具体接口路径
'''
url = f"{base_url.rstrip('/')}/chat/completions"    # 发给谁

# HTTP 请求头 「身份，发送格式」
headers = {                                         # 我是谁 + 发什么格式
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}


# [V0.7 新增] 固定使用一个 Session 文件
# [V0.14 准备] 使用新的 Session，避免读取 V0.13 的测试记录
session_path = Path("sessions/session-012-parent.jsonl")
explorer_session_path = Path("sessions/session-012-explorer.jsonl")
comparator_session_path = Path("sessions/session-012-comparator.jsonl")


# [V0.14 新增] 当前 Run 的执行进度
checkpoint_path = Path("runs/run-012.json")


# [V0.14 实验] 保证只模拟一次崩溃
crash_flag_path = (
    Path(__file__).resolve().parent
    / "test"
    / "crash_once.flag"
)


# [V0.9 新增] Skill 文件位置
skill_path =(
    Path(__file__).resolve().parent
    / "skills"
    / "code-review"
    / "SKILL.md"
    )


# [V0.10 新增] Extension 目录
extension_dir = (
    Path(__file__).resolve().parent
    / "extensions"
)


"""
将来可能有更多「终端渲染器」
event_handlers = [
    render_event,       # 终端显示
    log_to_file,        # 写日志
    save_to_db,         # 存数据库
    send_to_web,        # 推给网页
]
"""
# [V0.11 新增] 保存所有 Event Observer
event_handlers = [render_event]   # 观察者列表（目前只有终端渲染器）

# [V0.11 新增] 事件分发：向所有 Observer 发送事件
def emit(event_type, **data):
    event = {
        "type": event_type, 
        **data,             # 解包，把字典的键值对平铺进新字典，和 "type" 并列
    }
    
    for handler in event_handlers:
        handler(event)
        

# [V0.7 新增] 从磁盘恢复历史消息
def load_session():
    history = [system_messages]

    if not session_path.exists():
        return history
    
    with session_path.open("r", encoding="utf-8") as f:     # 打开文件
        for line in f:                                      # 逐行读
            if line.strip():                                # 跳过空行
                history.append(json.loads(line.strip()))    # 每行解析成消息，追加
    return history  


# [V0.9 新增] 只读取 Skill 开头的元数据： name 和 description
def load_skill_metadata(path):
    metadata = {}   # 结果字典

    for line in path.read_text(encoding="utf-8").splitlines()[1:]:      # 读文件、按行、跳过第一行(通常是 --- 分隔符)
        if line == "---":       # 遇到分隔线就停
            break
        
        key, value = line.split(":", 1)         # 按第一个冒号拆成键值
        metadata[key.strip()] = value.strip()
        
    return metadata


# [V0.8 修改] 消息同时进入 Session 和 Context，保证「当前会话能用」+「重启后能恢复」
def add_message(message):
    messages.append(message)  # 写入内存列表
    context_messages.append(message)  # 写入上下文列表
    
    session_path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
    
    with session_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n") # 写入 Session 磁盘文件


# [V0.9 新增] 加载 Skill 元数据
skill = load_skill_metadata(skill_path)


# [V0.13 修改] Parent 根据任务类型自主选择 SubAgent
system_messages = {
        "role": "system",
        "content": (
            # Parent 的基本行为
            "You are a concise coding assistant. "
            "Answer ordinary conversation directly. "
            "Use tools only when the user explicitly asks you to operate on files or run commands. "
            
            # Explorer：生成执行流程图
            "Use delegate_explorer to create execution flowcharts. "
            
            # Comparator：生成版本对比表
            "Use delegate_comparator to create comparison tables. "
            
            # Parent：组合结果并保留原始格式
            "Use the appropriate subagents and combine their results. "
                        
            # Session 由 Runtime 自动管理
            "Session persistence is handled automatically by the runtime.\n\n"
            
            # 告诉 Parent 当前有哪些 Skill
            "Available skills: \n"
            f"- {skill['name']}: {skill['description']}\n"
            f"  Before using this skill, read {skill_path.as_posix()} with the read tool."
        ),
    }


# [V0.13 新增] 两个 Child 的独立职责
EXPLORER_PROMPT = (
    "You are a flowchart subagent. "
    "Read relevant files and return a concise text flowchart using arrows."
)

COMPARATOR_PROMPT = (
    "You are a comparison subagent. "
    "Compare relevant files and return a concise Markdown table."
)


# [V0.7 修改] 启动时加载 Session
messages = load_session()

print(f"Session: {session_path}")
print(f"Explorer Session: {explorer_session_path}")
print(f"Comparator Session: {comparator_session_path}")
print(f"History: {len(messages) - 1} messages") # 减1 是因为第一条是系统消息


# [V0.8 新增] 实际发送给模型的 Context
context_messages = messages.copy()

# 上下文压缩（Compaction）的触发参数：决定「何时压、压完留多少」(教学版使用较小限制，方便触发 Compaction)
MAX_CONTEXT_MESSAGES = 8    # 消息超过这个数就触发压缩
RECENT_TURNS = 2            # 压缩后保留最近几轮对话 (user 说一句  →  assistant 回一句  = 1 轮)


    
# [V0.6 新增] Coding Tools 操作的工作目录，本项目的基准目录
workspace = Path.cwd().resolve()

# [V0.6 新增] 将相对路径限制在当前项目中
def resolve_path(path):
    # 第一步：翻译成真实路径     ← .resolve() 负责
    target = (workspace / path).resolve()
    # 第二步：判断是否越界       ← if 判断负责
    if target != workspace and workspace not in target.parents:
        raise ValueError("路径超出当前项目范围")
    return target


# [V0.6 修改] 读取项目内的任意文本文件
def read_file(path):
    return resolve_path(path).read_text(encoding="utf-8")

# [V0.6 新增] 创建或覆盖文件
def write_file(path, content):
    target = resolve_path(path)                         # 安全检查 + 转绝对路径
    target.parent.mkdir(parents=True, exist_ok=True)    # 确保父目录存在
    target.write_text(content, encoding="utf-8")        # 写入文件内容

    return f"已写入文件：{path}"                         # 返回结果

# [V0.6 新增] 替换文件中的一段文本
def edit_file(path, old_text, new_text):
    target = resolve_path(path)
    content = target.read_text(encoding="utf-8")
    
    if not old_text or old_text not in content:
        return "Error: 未找到需要替换的内容"
    
    content = content.replace(old_text, new_text, 1)    # 保证最多「改一处」的语义，避免误伤
    target.write_text(content, encoding="utf-8")
    
    return f"已编辑文件：{path}"

# [V0.6 新增] 在当前项目中执行命令
def run_bash(command):
    result = subprocess.run(
        command,
        shell=True,             # 交给 shell 解释执行
        cwd=workspace,          # 在项目目录里跑
        capture_output=True,    # 捕获输出，不直接打印
        text=True,              # 输出按文本解码，UTF-8(默认：stdout/stderr 是 bytes（字节）)
        timeout=30
    )
    return (
        f"Exit code 退出码: {result.returncode}\n"  # 命令正常结束返回 0；出错返回 非0
        f"stdout 标准输出：{result.stdout}\n"
        f"stderr 标准错误：{result.stderr}\n"
    )


# [V0.13 新增] 用指定职责和 Session，将独立任务交给 Subagent
def delegate_task(task, system_message, child_session_path):
    subagent_tools = [                         # 筛选 Subagent 的工具
        tool
        for tool in tools
        if tool["function"]["name"] == "read"  # 只保留 read
    ]
    
    return run_subagent(                       # 启动 Subagent
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


# [V0.6 修改] 注册 Coding Agent 使用的四个工具
"""
# 用一个字典集中登记所有工具：既告诉模型「有哪些工具、怎么用」，又保存「真正执行时调哪个函数
tool_registry
└── "read"        ← 工具名（key）
    └── { ... }         ← 这个工具的配置（value）
        ├── description  ← 给模型看：这工具干什么
        ├── parameters   ← 给模型看：参数格式（JSON Schema）
        └── execute      ← 给自己用：真正执行的函数
"""
tool_registry = {
    # 读取文件工具 read
    "read": {
        "description": "读取当前项目中的文本文件",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "相当于当前项目的文件路径"
                }
            },
            "required": ["path"]
        },
        "execute": read_file,
    },
    
    # 写入文件工具 write
    "write": {
        "description": "创建或覆盖项目中的文件",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "相当于当前项目的文件路径"
                },
                "content":{
                    "type": "string",
                    "description": "要写入的完整内容",
                },
            },
            "required": ["path", "content"],
        },
        "execute": write_file,
    },
    
    # 编辑文件工具 edit
    "edit":{
        "description": "编辑项目中的文件，替换指定内容",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "相当于当前项目的文件路径"
                },
                "old_text": {
                    "type": "string",
                    "description": "要被替换的旧内容"
                },
                "new_text": {
                    "type": "string",
                    "description": "要替换成的新内容"
                },
            },
            "required": ["path", "old_text", "new_text"],
        },
        "execute": edit_file,
    },
    
    # 工具 bash
    "bash":{
        "description": "执行 bash 命令",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 bash 命令"
                }
            },
            "required": ["command"]
        },
        "execute": run_bash,
    },
    
    # [V0.13 修改] Explorer：分析结构和执行流程
    "delegate_explorer":{
        "description": "Create a text flowchart that explains a file's execution flow.",
        "parameters":{
            "type":"object",
            "properties":{
                "task":{
                    "type":"string",
                    "description":"The exploration task."
                }
            },
            "required": ["task"],
        },
        "execute": delegate_explorer,
    },
    
    # [V0.13 修改] Comparator：生成版本对比表
    "delegate_comparator":{
        "description": "Compare files or versions and return a concise Markdown table.",
        "parameters":{
            "type":"object",
            "properties":{
                "task":{
                    "type":"string",
                    "description":"The comparison task for the SubAgent.",
                }
            },
            "required": ["task"],
        },
        "execute": delegate_comparator,
    },
}


"""
 extensions/
├── my_tool.py
└── another.py

load_extensions()
        ↓
pi = ExtensionAPI()                 ← 创建共享接口
        ↓
遍历 sorted(["my_tool.py", "another.py"])
        ↓
┌─────────────────────────────────────────┐
│ 对每个文件：                              │
│  ① spec_from_file_location → spec        │
│  ② module_from_spec        → 空模块       │
│  ③ exec_module             → 执行，填充   │
│  ④ module.setup(pi)        → 注册能力     │
│  ⑤ print("loaded: ...")                  │
└─────────────────────────────────────────┘
        ↓
所有插件的能力都注册进 pi（进而进主程序）
"""
# [V0.10 新增] 提供给 Extension 的最小 API
class ExtensionAPI:
    def register_tool(self, name, description, parameters, execute):
        tool_registry[name] = {
            "description": description,
            "parameters": parameters,
            "execute": execute,
        }

# [V0.10 新增] 加载 extensions 目录中的模块
def load_extensions():
    pi = ExtensionAPI()     # 创建 API 对象
    
    for path in sorted(extension_dir.glob("*.py")):  # 遍历 extensions 目录下的所有 .py 文件
        spec = importlib.util.spec_from_file_location(f"extension_{path.stem}", path)  # 创建模块规范
        module = importlib.util.module_from_spec(spec)      # 用规格创建模块对象
        spec.loader.exec_module(module)                     # 执行模块（真正导入）
        
        module.setup(pi)  # 调用模块的 setup 函数，传入 ExtensionAPI 实例，注册能力
        print(f"Extension loaded: {path.stem}")

load_extensions()



# [V0.13 新增] 允许 Parent 启动 Subagent
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


# [V0.5 修改] 从 Tool Registry 生成发送给模型的 Tool Schema
'''
tools 是一个工具列表
tools = [
    read_file工具,
    write_file工具,
    bash工具,
    ...
]
'''
tools = [
    {
        "type": "function",         # 表示这是函数类型的工具，它告诉模型：这个工具最终会由程序中的某个函数来执行
        "function":{                # 描述函数的名字、用途和参数
            "name": tool_name,
            "description": tool["description"],
            "parameters": tool["parameters"],
        },
    }
    
    for tool_name, tool in tool_registry.items()
]


"""
完整 messages
      ↓ 复制
context_messages
      ↓ 对旧消息进行压缩
system + summary + 最近几轮消息
      ↓
发送给模型
"""
# [V0.8 新增] 将旧消息总结为简短摘要
def summarize_messages(old_messages):
    # 构造一个新的 request_data，目的不是继续对话，而是「请模型做一次总结」
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
                "content":json.dumps(old_messages, ensure_ascii=False),
            },
        ],
    }

    response = requests.post(
        url,                # 请求地址
        headers=headers,    # 请求头【身份，发送格式】
        json=request_data,  # 请求体【模型，消息】
        timeout=20,
    )
    
    response.raise_for_status()
    
    # 提取模型回答
    data = response.json()          # 将响应 JSON 转回 Python 对象(这里为字典)
    assistant_message = data["choices"][0]["message"]["content"]    # 摘要请求不发送 tools，因为这里只需要总结，不需要工具调用。
    
    return assistant_message


# [V0.8 新增] 压缩旧 Context，保留最近两轮对话
def compact_context():
    global context_messages
    
    # 消息数没超过 8（MAX_CONTEXT_MESSAGES）→ 直接返回，什么都不做
    if len(context_messages) <= MAX_CONTEXT_MESSAGES:
        return

    # 找出所有 user 消息的下标
    """
    为什么要找 user 的下标?
    因为「轮（turn）」是按 user 消息划分的——每个 user 消息开启一轮。
    要保留「最近 N 轮」，就得按 user 的位置切
    """
    user_indexes = [
        index
        for index, message in enumerate(context_messages)
        if message["role"] == "user"
    ]
    
    # user 消息数 ≤ 2（RECENT_TURNS）→ 说明总共就一两轮，没有「更早的」可压 → 返回
    if len(user_indexes) <= RECENT_TURNS:
        return
    
    
    # 找到分界点: 从倒数第二个用户回合开始保留
    split_index = user_indexes[-RECENT_TURNS]
    
    old_messages = context_messages[1:split_index]      # 要压缩的旧消息(从下标 1 开始 → 跳过下标 0 的 system 消息)
    recent_messages = context_messages[split_index:]    # 要保留的最近消息
    
    # 调模型做摘要
    summary = summarize_messages(old_messages)
    
    # 重组上下文
    context_messages = [
        system_messages,
        {
            "role": "system",
            "content": f"Summary of earlier conversation:\n{summary}"
        },
        *recent_messages,   # *是解包操作符，把列表里的元素一个个平铺进新列表
    ]
    
    print(
        f"Context compacted: "
        f"{len(old_messages)} messages → 1 summary"
    )
    
    
# [V0.8 修改] 只把构造后的 Context 发给模型
# [V0.13 修改] Parent 和 Child(Subagent) 可以使用不同工具
def call_model(context, available_tools=None):
    if available_tools is None:
        available_tools = tools
    
    ## [V0.3 修改] 构造请求体：把消息，工具说明发送给模型
    request_data = {
        "model": model,
        "messages": context,
        "tools": available_tools,
        "tool_choice": "auto"   # 告诉模型在什么时候应该调用工具，"auto" 表示模型自行决定
    }
    
    ## 将请求体发给模型：发出 HTTP 请求 「这次请求，我到底要送过去什么？」
    response = requests.post(
        url,                # 请求地址
        headers=headers,    # 请求头【身份，发送格式】
        json=request_data,  # 请求体【模型，消息】
        timeout=40,
    )
    
    response.raise_for_status()     # 遇到 4xx 或 5xx 响应时主动抛出异常

    # 提取模型回答
    data = response.json()          # 将响应 JSON 转回 Python 对象(这里为字典)
    assistant_message = data["choices"][0]["message"]
    
    # [V0.8 新增] 不保存模型内部 reasoning,让 Session 和 Context 保持精简
    assistant_message.pop("reasoning", None)
    
    return assistant_message


# [V0.14 新增] 检查是否存在未完成任务
checkpoint = load_checkpoint(checkpoint_path)       # 读档

resume_run = bool(                                      # 判断是否要恢复(resume_run 是个布尔值 True / False)
    checkpoint          
    and checkpoint.get("status") in ("RUNNING", "WAITING_TOOL")  
)

pending_tool_calls = (                              # 取出待执行的工具
    checkpoint["tool_calls"]
    if resume_run and checkpoint["status"] == "WAITING_TOOL"
    else None
)


'''
外层循环
  → 有未完成 Run：跳过 input，恢复旧任务
  → 没有未完成 Run：正常读取用户输入

内层循环
  → 已有待执行 Tool Call：跳过模型调用，直接执行工具
  → 没有 Tool Call：正常调用模型

工具完成
  → tool_calls = None
  → 再次调用模型生成最终回答
'''
# [V0.4 新增] (外层 while)主循环：持续接收用户输入，接收新任务或恢复旧任务，直到用户输入 /exit 退出
while True:
    
    # [V0.14 新增] 优先恢复未完成任务
    if resume_run:
        print(f"Run resumed: {checkpoint['status']}")
        
        tool_calls = pending_tool_calls
        resume_run = False  # 只恢复一次，避免无限循环
    
    else:
        # 构造消息
        ## 获取用户消息
        user_message = input("> ")
    
        # [V0.2 新增] 提供主动结束会话的方式
        if user_message == "/exit":
            break
    
        # [V0.7 修改] 保存用户消息到内存和 Session
        add_message(
            {
                "role":"user",
                "content": user_message,
            }
        )

        # [V0.14 新增] 新任务开始
        save_checkpoint(
            checkpoint_path,
            "RUNNING",
        )
        
        tool_calls = None  # 新任务没有待执行的工具调用
    
    
    # [V0.4 新增] (内层 while)内循环 Agent Loop：模型与工具持续交互，直到模型不再调用工具(即没有 Tool Call)
    while True:
        # [V0.14 修改] 恢复时已有 Tool Call，不再重复调用模型
        if tool_calls is None:
            
            # [V0.8 新增] 调用模型前检查 Context 是否需要压缩
            compact_context()
        
            # [V0.7 修改] 保存模型消息到内存和 Session
            assistant_message = call_model(context_messages)
            add_message(assistant_message)  # 保存模型消息到内存和 Session
        
            tool_calls = assistant_message.get("tool_calls")

            # [V0.11 修改] 没有 Tool Call，发送 Agent 完成事件
            # 以前是：print(f"Answer: {assistant_message['content']}")
            if not tool_calls:
                # [V0.14 新增] 任务完成，保存状态
                save_checkpoint(
                    checkpoint_path,
                    "SUCCEEDED",
                )
                
                emit(
                    "agent_end", 
                    answer=assistant_message["content"],
                )
                break
            
        
            # [V0.14 新增] Tool Call 已产生，记录待执行状态
            save_checkpoint(
                checkpoint_path,
                "WAITING_TOOL",
                tool_calls,
            )
        
        
        # [V0.4 修改] 执行本轮模型发出的所有 Tool Call
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_arguments = json.loads(tool_call["function"]["arguments"])

            # [V0.5 新增] 根据工具名称从 Registry 查找工具
            tool = tool_registry.get(tool_name)
            if not tool:
                raise RuntimeError(f"未知工具: {tool_name}")

            # [V0.11 修改] 发送工具开始事件
            # 以前是：print(f"调用工具 Tool Call: {tool_name}, 参数: {tool_arguments}")
            emit(
                "tool_start",
                name=tool_name,
                arguments=tool_arguments,
            )
            
            
            # [V0.14 实验] Tool Call 已保存，但 Tool 尚未执行
            if not crash_flag_path.exists():
                crash_flag_path.parent.mkdir(parents=True, exist_ok=True)
                crash_flag_path.write_text("crash once", encoding="utf-8")
                raise RuntimeError("Simulated crash before Tool Result")
            
            
            # [V0.6 修改] 工具错误也作为 Tool Result 返回给模型
            try:
                # [V0.12 新增] 执行工具前先检查权限
                sandbox.check(tool_name)
                tool_result = tool["execute"](**tool_arguments)
            except Exception as e:
                tool_result = f"Error: {e}"


            # [V0.11 修改] 发送工具完成事件
            # 以前：print(f"工具执行结果 Tool Result: \n{tool_result}")
            emit(
                "tool_end",
                result=tool_result,
            )
    
            # [V0.7 修改] 保存 Tool Result 到内存和 Session
            add_message(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result,
                }
            )
            
            
        # [V0.14 新增] 本轮 Tool Call 已执行完，更新状态，清空待执行列表
        save_checkpoint(
            checkpoint_path,
            "RUNNING",
        )
        
        tool_calls = None
