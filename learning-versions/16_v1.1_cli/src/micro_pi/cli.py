import argparse
import sys
import warnings
from getpass import GetPassWarning, getpass
from importlib.metadata import version
from pathlib import Path

from .app import Workspace, create_runtime
from .config import ConfigError, ModelConfig, config_path, load_config, save_config
from .provider import Provider, ProviderError


def configure(path):
    if not (sys.stdin.isatty() and sys.stderr.isatty()):
        raise ConfigError("请在交互终端运行 micro-pi init，或提供完整的 MICRO_PI_* 环境变量。")

    print("首次配置可使用任意兼容 OpenAI Chat Completions 的模型服务。")
    base_url = input("模型 API 根地址 [https://api.deepseek.com]: ").strip() or "https://api.deepseek.com"
    model = input("模型名称: ")
    with warnings.catch_warnings():
        warnings.simplefilter("error", GetPassWarning)
        api_key = getpass("API Key（输入隐藏）: ")

    config = ModelConfig(base_url, model, api_key)
    print("正在验证模型连接…")
    reply = Provider(config).call([{"role": "user", "content": "Reply with OK."}])
    if not (reply.get("content") or "").strip():
        raise ProviderError("模型没有返回文本，请检查模型名称和服务配置。")

    save_config(path, config)
    print("模型连接成功，配置已保存。")
    return config


def chat(config, settings_path):
    workspace = Workspace(Path.cwd(), settings_path)
    runtime = create_runtime(workspace, Provider(config))
    print(f"micro-pi · {config.model} · {workspace.path}")
    print(f"History: {len(runtime.session.messages)} messages · 输入 /exit 退出")

    pending = runtime.load_pending_run()
    if pending:
        print(f"Run resumed: {pending['status']}")
        tool_calls = pending["tool_calls"] if pending["status"] == "WAITING_TOOL" else None
        runtime.run_agent_loop(tool_calls)
    elif not runtime.session.messages:
        print("试一试：请使用 word_count 统计 one two three four 的词数。")

    while True:
        try:
            user_message = input("> ")
        except EOFError:
            break
        if user_message.strip() == "/exit":
            break
        if user_message.strip():
            runtime.start_run(user_message)


# [V1.1 新增] 保持导入无副作用，由终端命令或 python -m 调用
def main(argv=None):
    parser = argparse.ArgumentParser(prog="micro-pi", description="learn-pi 教程的终端 Agent")
    parser.add_argument("--version", action="version", version=f"micro-pi {version('learn-pi')}")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("init", help="验证并保存模型配置")
    args = parser.parse_args(argv)

    setup_in_progress = args.command == "init"
    try:
        path = config_path()
        config = None if setup_in_progress else load_config(path)
        if config is None:
            setup_in_progress = True
            config = configure(path)
        if args.command != "init":
            setup_in_progress = False
            chat(config, path)
    except (KeyboardInterrupt, EOFError):
        print("\n已取消配置。" if setup_in_progress else "\n已退出 micro-pi。", file=sys.stderr)
        return 130 if sys.exc_info()[0] is KeyboardInterrupt else 1
    except GetPassWarning:
        print("当前终端无法隐藏密钥输入，请换用支持隐藏输入的终端。", file=sys.stderr)
        return 1
    except ProviderError as error:
        print(str(error), file=sys.stderr)
        if not setup_in_progress:
            print("修复连接后重新运行 micro-pi，继续已保存的任务。", file=sys.stderr)
        return 1
    except ConfigError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, RuntimeError):
        print("无法完成当前操作，请检查工作区的状态文件和读写权限。", file=sys.stderr)
        return 1
    return 0
