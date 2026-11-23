import os

import json
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
# [V1.0 新增] 模型服务入口
from provider import Provider
# [V1.0 新增] Session 管理
from session import Session
# [V1.0 新增] Context 管理
from context import Context
# [V1.0 新增] Tool Registry 管理
from tool_registry import ToolRegistry
# [V1.0 修改] 导入 Agent Runtime
from runtime import Runtime

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
# [V1.0 新增] 创建统一的模型服务入口
provider = Provider(base_url, model, api_key)


# [V0.7 新增] 固定使用一个 Session 文件
# [V1.0 准备] 使用新的 Session，避免读取 V0.14 的测试记录
session_path = Path("sessions/session-013-parent.jsonl")
explorer_session_path = Path("sessions/session-013-explorer.jsonl")
comparator_session_path = Path("sessions/session-013-comparator.jsonl")


# [V1.0 准备] 使用新的 Checkpoint，避免读取 V0.14 的执行进度
checkpoint_path = Path("runs/run-013.json")


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
        

# [V0.9 新增] 只读取 Skill 开头的元数据： name 和 description
def load_skill_metadata(path):
    metadata = {}   # 结果字典

    for line in path.read_text(encoding="utf-8").splitlines()[1:]:      # 读文件、按行、跳过第一行(通常是 --- 分隔符)
        if line == "---":       # 遇到分隔线就停
            break
        
        key, value = line.split(":", 1)         # 按第一个冒号拆成键值
        metadata[key.strip()] = value.strip()
        
    return metadata


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


# [V1.0 修改] 通过 Session 对象恢复历史消息
session = Session(session_path)
history = session.load()  # 读档恢复历史消息


print(f"Session: {session_path}")
print(f"Explorer Session: {explorer_session_path}")
print(f"Comparator Session: {comparator_session_path}")
print(f"History: {len(history)} messages")          # history 不包含 System Message

# [V1.0 修改] 创建 Context 对象，使用系统提示词和历史消息初始化
context = Context(system_messages, history)


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
        provider.call,
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


# [V1.0 修改] 使用已有工具初始化 Tool Registry
"""
# 用一个字典集中登记所有工具：既告诉模型「有哪些工具、怎么用」，又保存「真正执行时调哪个函数
tool_registry
└── "read"        ← 工具名（key）
    └── { ... }         ← 这个工具的配置（value）
        ├── description  ← 给模型看：这工具干什么
        ├── parameters   ← 给模型看：参数格式（JSON Schema）
        └── execute      ← 给自己用：真正执行的函数
"""
tool_registry = ToolRegistry({
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
})


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
# [V1.0 修改] Extension 通过 Tool Registry 注册工具
class ExtensionAPI:
    def register_tool(self, name, description, parameters, execute):
        tool_registry.register(name, description, parameters, execute)

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
# [V1.0 修改] 从 Tool Registry 生成发送给模型的 Tool Schema
tools = tool_registry.schemas()


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

---------------------------------

main.py
  ├── 初始化对象
  ├── 恢复任务或读取终端输入
  └── 调用 run_agent_loop(...)

runtime.py (内层循环)
  └── run_agent_loop()
      ├── 调用模型
      ├── 执行工具
      └── 更新 Checkpoint
'''
# [V1.0 新增] 创建 Runtime，集中保存 Agent Loop 的依赖
runtime = Runtime(
    context,
    provider,
    tools,
    tool_registry,
    sandbox,
    emit,
    session,
    checkpoint_path,
    MAX_CONTEXT_MESSAGES,
    RECENT_TURNS,
)

# [V1.0 修改] 由 Runtime 读取未完成任务
checkpoint = runtime.load_pending_run()
resume_run = checkpoint is not None
pending_tool_calls = (
    checkpoint["tool_calls"]
    if resume_run and checkpoint["status"] == "WAITING_TOOL"
    else None
)

# [V0.4 新增] (外层 while)主循环：持续接收用户输入，接收新任务或恢复旧任务，直到用户输入 /exit 退出
while True:
    
    # [V0.14 新增] 优先恢复未完成任务
    if resume_run:
        print(f"Run resumed: {checkpoint['status']}")
        
        tool_calls = pending_tool_calls
        resume_run = False  # 只恢复一次，避免无限循环
        # [V1.0 修改] 将待恢复的任务交给 Runtime
        runtime.run_agent_loop(tool_calls)
    
    else:
        # 构造消息
        ## 获取用户消息
        user_message = input("> ")
    
        # [V0.2 新增] 提供主动结束会话的方式
        if user_message == "/exit":
            break

        # [V1.0 修改] 新任务交给 Runtime 保存并执行
        runtime.start_run(user_message)

    
