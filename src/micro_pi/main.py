import os

import requests
from dotenv import load_dotenv


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

/embeddings	文本向量化
/images/generations	画图
/audio/transcriptions	语音转文字
/models	列出可用模型
'''
url = f"{base_url.rstrip('/')}/chat/completions"    # 发给谁

# HTTP 请求头 「身份，发送格式」
headers = {                                         # 我是谁 + 发什么格式
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 构造消息
## 获取用户消息
user_message = input("> ")

## messages 就是本次发送给模型的上下文
request_data = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_message}
    ]
}


# 发出 HTTP 请求 「这次请求，我到底要送过去什么？」
response = requests.post(                           
    url,                # 请求地址
    headers=headers,    # 请求头【身份，发送格式】
    json=request_data,  # 请求体【模型，消息】
    timeout=20
)

response.raise_for_status()     # 遇到 4xx 或 5xx 响应时主动抛出异常


# 提取模型回答
data = response.json()          # 将响应 JSON 转回 Python 对象(这里为字典)
answer = data["choices"][0]["message"]["content"]
print(f"Answer: {answer}")  