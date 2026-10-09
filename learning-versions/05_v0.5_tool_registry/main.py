import os

import json
import requests
from dotenv import load_dotenv
from pathlib import Path


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


# [V0.2 新增] 创建消息历史：在循环外创建，整个会话共同使用
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant."
    }
]


# [V0.3 新增] 真正读取文件的是 Python，而不是模型
def read_file(path):
    if path != "README.md":
        return "Error: 当前版本只允许读取 README.md"
    return Path(path).read_text(encoding="utf-8")


# [V0.5 新增] Tool Registry (工具注册表)：集中保存工具说明和执行函数
"""
# 用一个字典集中登记所有工具：既告诉模型「有哪些工具、怎么用」，又保存「真正执行时调哪个函数
tool_registry
└── "read_file"        ← 工具名（key）
    └── { ... }         ← 这个工具的配置（value）
        ├── description  ← 给模型看：这工具干什么
        ├── parameters   ← 给模型看：参数格式（JSON Schema）
        └── execute      ← 给自己用：真正执行的函数
"""
tool_registry = {
    "read_file": {
        "description": "读取项目中的 README.md 文件",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "enum": ["README.md"],
                    "description": "文件路径"
                }
            },
            "required": ["path"]
        },
        "execute": read_file,
    }
}


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


# [V0.3 新增] 完成一次模型调用
def call_model(messages):
    
    ## [V0.3 修改] 构造请求体：把消息，工具说明发送给模型
    request_data = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto"   # 告诉模型在什么时候应该调用工具，"auto" 表示模型自行决定
    }
    
    ## 将请求体发给模型：发出 HTTP 请求 「这次请求，我到底要送过去什么？」
    response = requests.post(
        url,                # 请求地址
        headers=headers,    # 请求头【身份，发送格式】
        json=request_data,  # 请求体【模型，消息】
        timeout=20
    )
    
    response.raise_for_status()     # 遇到 4xx 或 5xx 响应时主动抛出异常

    # 提取模型回答
    data = response.json()          # 将响应 JSON 转回 Python 对象(这里为字典)
    assistant_message = data["choices"][0]["message"]
    
    return assistant_message


# [V0.2 新增] 构造循环：循环接收输入，实现多轮对话
# [V0.4 新增] 主(外)循环：持续接收用户输入，直到用户输入 /exit 退出
while True:

    # 构造消息
    ## 获取用户消息
    user_message = input("> ")
    
    # [V0.2 新增] 提供主动结束会话的方式
    if user_message == "/exit":
        break
    
    # [V0.2 新增] 保存本轮用户消息到历史
    messages.append(
        {
            "role":"user",
            "content": user_message,
        }
    )
    
    
    # [V0.4 新增] 内循环 Agent Loop：模型与工具持续交互，直到模型不再调用工具(即没有 Tool Call)
    while True:
        
        # [V0.4 修改] 每轮循环都让模型决定下一步
        assistant_message = call_model(messages)
        messages.append(assistant_message)
        
        tool_calls = assistant_message.get("tool_calls")

        # [V0.4 新增] 没有 Tool Call，说明任务已经完成
        if not tool_calls:
            print(f"Answer: {assistant_message['content']}")
            break
        
        # [V0.4 修改] 执行本轮模型发出的所有 Tool Call
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_arguments = json.loads(tool_call["function"]["arguments"])

            # [V0.5 新增] 根据工具名称从 Registry 查找工具
            tool = tool_registry.get(tool_name)
            if not tool:
                raise RuntimeError(f"未知工具: {tool_name}")
    
            print(f"调用工具 Tool Call: {tool_name}, 参数: {tool_arguments}")
    
            # [V0.5 修改] 使用模型生成的参数执行对应工具
            tool_result = tool["execute"](**tool_arguments)
    
            print(f"工具执行结果 Tool Result: \n{tool_result}")
    
            # [V0.3 新增] 把 Tool Result 返回给对应的 Tool Call
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result,
                }
            )


# ---------仅测试：查看message--------   
print("\n完整 Messages：")
print(
    json.dumps(
        messages,
        ensure_ascii=False,
        indent=2,
    )
)