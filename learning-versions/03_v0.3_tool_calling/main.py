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

# [V0.3 新增] 创建Tool Schema(工具定义)：告诉模型有哪些工具，以及应该如何调用
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
            "name": "read_file",
            "description": "读取项目中的 README.md 文件",
            "parameters": {         # 类似 JSON Schema 的格式，描述 path 应该是什么类型、是否必填，以及允许哪些值
                "type": "object",   # 工具参数应该是一个 JSON 对象
                "properties": {     # 定义这个参数对象里可以有哪些字段(现只定义 path 字段)
                    "path": {
                        "type": "string",
                        "enum": ["README.md"],   # 限制可选值，只允许读取 README.md
                        "description": "文件路径"
                    }
                },
                "required": ["path"],   # 指定哪些字段是必填的，模型调用 read_file 时必须提供 path
            },
        },
    }
]

# [V0.3 新增] 真正读取文件的是 Python，而不是模型
def read_file(path):
    if path != "README.md":
        return "Error: V0.3只允许读取 README.md"
    return Path(path).read_text(encoding="utf-8")

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
            "content": user_message
        }
    )
    
    # [V0.3 新增] 调用模型获取回答
    # 第一次调用：模型决定直接回答还是调用工具
    assistant_message = call_model(messages)
    messages.append(assistant_message)
    
    tool_calls = assistant_message.get("tool_calls")

    # 没有 Tool Call，按普通对话处理
    if not tool_calls:
        print(f"Answer: {assistant_message['content']}")
        continue
    
    # [V0.3 新增] 解析第一个 Tool Call
    """
    assistant_message = {
    "role": "assistant",
    "content": None,                    # 决定调工具时，content 常常是 None
    "tool_calls": [                     # ← 这就是 tool_calls，一个列表
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": "{\"path\":\"README.md\"}"   # ← 注意是字符串
            }
        }
    ]
}
    """
    tool_call = tool_calls[0]   # 取出第一个工具调用
    tool_name = tool_call["function"]["name"]
    tool_arguments = json.loads(tool_call["function"]["arguments"])
    
    if tool_name != "read_file":
        raise RuntimeError(f"未知工具: {tool_name}")
    
    print(f"调用工具 Tool Call: {tool_name}, 参数: {tool_arguments}")
    
    # [V0.3 新增] Python Runtime 执行工具
    tool_result = read_file(tool_arguments["path"])
    
    print(f"工具执行结果 Tool Result: \n{tool_result}")
    
    # [V0.3 新增] 把 Tool Result 返回给对应的 Tool Call
    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": tool_result,
        }
    )
    
    
    # [V0.3 新增] 第二次调用：根据 Tool Result 生成最终回答
    final_message = call_model(messages)
    # 保存最终回答到历史
    messages.append(final_message)
    
    print(f"最终回答 Final Message: {final_message['content']}")


# ---------仅测试：查看message--------   
print("\n完整 Messages：")
print(
    json.dumps(
        messages,
        ensure_ascii=False,
        indent=2,
    )
)