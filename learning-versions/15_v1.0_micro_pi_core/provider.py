import requests

'''
Provider
 ├── 知道怎么发 HTTP 请求
 ├── 知道怎么处理 API Key、Base URL、超时
 ├── 知道怎么解析响应
 └── 对外只暴露一个简单的 call() 方法
'''
class Provider:
    # [V1.0 新增] 保存模型服务配置
    def __init__(self, base_url, model, api_key):
        self.model = model
        self.base_url = f"{base_url.rstrip('/')}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",   
        }
    
    # [V1.0 新增] 统一调用模型
    def call(self, messages, tools=None):
        request_data = {
            "model": self.model,
            "messages": messages,
        }
        
        if tools:
            request_data["tools"] = tools
            request_data["tool_choice"] = "auto"
        
        response = requests.post(
            self.base_url, 
            headers=self.headers, 
            json=request_data,
            timeout=40,
            )
        
        response.raise_for_status()
        
        assistant_message = response.json()["choices"][0]["message"]
        assistant_message.pop("reasoning", None)
        
        return assistant_message