import requests


class ProviderError(RuntimeError):
    """An error safe to display in the terminal without the request or response body."""


class Provider:
    # [V1.1 修改] 配置由 CLI 传入，模型调用失败时生成可读的终端提示
    def __init__(self, config):
        self.model = config.model
        self.url = f"{config.base_url.rstrip('/')}/chat/completions"
        self.headers = {"Authorization": f"Bearer {config.api_key}"}

    def call(self, messages, tools=None):
        request_data = {"model": self.model, "messages": messages}
        if tools:
            request_data.update(tools=tools, tool_choice="auto")

        try:
            response = requests.post(
                self.url, headers=self.headers, json=request_data,
                timeout=40, allow_redirects=False,
            )
            response.raise_for_status()
        except requests.HTTPError as error:
            status = error.response.status_code
            if status in (401, 403):
                raise ProviderError(f"模型鉴权失败（HTTP {status}），请检查 API Key 和账号权限。") from None
            raise ProviderError(f"模型请求失败（HTTP {status}），请检查模型地址、名称和服务状态。") from None
        except requests.exceptions.SSLError:
            raise ProviderError("模型 TLS 连接失败，请检查网络和代理设置。") from None
        except requests.RequestException:
            raise ProviderError("无法连接模型服务，请检查网络、代理和模型地址。") from None

        if not response.ok or 300 <= response.status_code < 400:
            raise ProviderError("模型地址返回重定向，请填写实际服务的 API 根地址。")

        try:
            message = response.json()["choices"][0]["message"]
            if not isinstance(message, dict) or message.get("role") != "assistant":
                raise ValueError
            if not message.get("tool_calls") and not isinstance(message.get("content"), str):
                raise ValueError
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProviderError("模型响应无法解析，请确认服务兼容 Chat Completions。") from None

        message.pop("reasoning", None)
        return message
