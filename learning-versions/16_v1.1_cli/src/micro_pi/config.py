import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit


ENV_NAMES = {
    "base_url": "MICRO_PI_BASE_URL",
    "model": "MICRO_PI_MODEL",
    "api_key": "MICRO_PI_API_KEY",
}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ModelConfig:
    base_url: str
    model: str
    api_key: str = field(repr=False)

    def __post_init__(self):
        for name in ENV_NAMES:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ConfigError(f"缺少配置项 {ENV_NAMES[name]}。")
            object.__setattr__(self, name, value.strip())

        if any(char.isspace() for char in self.base_url):
            raise ConfigError("模型 API 地址不能包含空白字符。")
        try:
            address = urlsplit(self.base_url)
            address.port  # 校验显式指定的端口
        except ValueError:
            raise ConfigError("模型 API 地址格式不正确。") from None

        loopback = address.hostname in {"localhost", "127.0.0.1", "::1"}
        if not address.hostname or not (
            address.scheme == "https" or (loopback and address.scheme == "http")
        ):
            raise ConfigError("模型 API 需要 HTTPS，本机服务可使用 HTTP。")
        if address.username is not None or address.password is not None or address.query or address.fragment:
            raise ConfigError("模型 API 地址不能包含账号、查询参数或片段。")
        if address.path.rstrip("/").endswith("/chat/completions"):
            raise ConfigError("请填写 API 根地址，去掉末尾的 /chat/completions。")


def config_path():
    return Path.home() / ".micro-pi" / "config.json"


# [V1.1 新增] 完整的环境变量配置优先，避免混用不同来源的地址和密钥
def load_config(path):
    values = {name: os.getenv(var, "") for name, var in ENV_NAMES.items()}
    if any(values.values()):
        return ModelConfig(**values)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (ValueError, OSError):
        raise ConfigError("无法读取已保存的配置，请运行 micro-pi init 重新配置。") from None

    if not isinstance(data, dict):
        raise ConfigError("配置格式无效，请运行 micro-pi init 重新配置。")
    return ModelConfig(**{name: data.get(name) for name in ENV_NAMES})


# [V1.1 新增] 验证模型连接后再替换配置，避免取消或写到一半损坏原配置
def save_config(path, config):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temp_path = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as file:
            temp_path = Path(file.name)
            json.dump({name: getattr(config, name) for name in ENV_NAMES}, file, indent=2)
            file.write("\n")
        temp_path.replace(path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
