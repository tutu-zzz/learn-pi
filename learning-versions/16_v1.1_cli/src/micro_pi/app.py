import subprocess
from importlib.resources import files

from .context import Context
from .extensions import word_count
from .renderer import render_event
from .runtime import Runtime
from .sandbox import Sandbox
from .session import Session
from .subagent import run_subagent
from .tool_registry import ToolRegistry


SKILL_ID = "@skill/code-review"
ALLOWED_TOOLS = {"read", "write", "edit", "word_count", "delegate_explorer", "delegate_comparator"}


# [V1.1 新增] Skill 通过包资源读取，安装位置可以与工作区完全分开
def load_skill():
    return files("micro_pi").joinpath("skills", "code-review", "SKILL.md").read_text(encoding="utf-8")


class Workspace:
    def __init__(self, path, config_file):
        self.path = path.resolve()
        self.state_dir = self.path / ".micro-pi"
        if self.state_dir.resolve() != self.state_dir:
            raise ValueError("工作区 .micro-pi 目录不能指向其他位置。")
        self.config_dir = config_file.parent.resolve()

    # [V1.1 修改] 工作区文件与程序资源分别访问，内部状态和配置不开放给模型
    def resolve_file(self, path):
        if path.startswith("@skill/"):
            raise ValueError("内置 Skill 只能通过 read 读取。")

        target = (self.path / path).resolve()
        if not target.is_relative_to(self.path):
            raise ValueError("路径超出当前工作区。")
        if target.is_relative_to(self.state_dir) or target.is_relative_to(self.config_dir):
            raise ValueError("工具不能访问 micro-pi 的内部配置或状态。")
        if target.name.lower() == ".env":
            raise ValueError("工具不能访问 .env 文件。")
        return target

    def read_file(self, path):
        if path == SKILL_ID:
            return load_skill()
        return self.resolve_file(path).read_text(encoding="utf-8")

    def write_file(self, path, content):
        target = self.resolve_file(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"已写入文件：{path}"

    def edit_file(self, path, old_text, new_text):
        target = self.resolve_file(path)
        content = target.read_text(encoding="utf-8")
        if not old_text or old_text not in content:
            return "Error: 未找到需要替换的内容"
        target.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
        return f"已编辑文件：{path}"

    def run_bash(self, command):
        # 与 V1.0 一样保留 schema，默认工具白名单拒绝此工具
        result = subprocess.run(
            command, shell=True, cwd=self.path, capture_output=True, text=True, timeout=30,
        )
        return f"Exit code: {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"


def make_registry(workspace, provider):
    registry = ToolRegistry({})

    def register(name, description, execute, **arguments):
        schema = {
            "type": "object",
            "properties": {
                key: {"type": "string", "description": value} for key, value in arguments.items()
            },
            "required": list(arguments),
        }
        registry.register(name, description, schema, execute)

    def delegate(task, role, system_prompt):
        tools = [tool for tool in registry.schemas() if tool["function"]["name"] == "read"]
        return run_subagent(
            task, system_prompt, provider.call, workspace.read_file, tools,
            workspace.state_dir / f"{role}.jsonl",
        )

    def explorer(task):
        return delegate(task, "explorer", "Read relevant files and return a concise text flowchart using arrows.")

    def comparator(task):
        return delegate(task, "comparator", "Compare relevant files and return a concise Markdown table.")

    register("read", "读取工作区的文本文件或内置 Skill。", workspace.read_file,
             path=f"工作区内的文件路径，或 {SKILL_ID}")
    register("write", "创建或覆盖工作区文件。", workspace.write_file,
             path="文件路径", content="要写入的内容")
    register("edit", "替换工作区文件中的第一处匹配内容。", workspace.edit_file,
             path="文件路径", old_text="旧内容", new_text="新内容")
    register("bash", "执行命令。", workspace.run_bash, command="命令")
    register("delegate_explorer", "Create a text flowchart from relevant files.", explorer, task="分析任务")
    register("delegate_comparator", "Compare files and return a Markdown table.", comparator, task="对比任务")

    # [V1.1 修改] 从已安装的包加载内置扩展，再通过同一个注册表生成 Schema
    class ExtensionAPI:
        def register_tool(self, name, description, parameters, execute):
            registry.register(name, description, parameters, execute)

    word_count.setup(ExtensionAPI())
    return registry


def create_runtime(workspace, provider):
    metadata = load_skill().split("---", 2)[1]
    skill = dict(line.strip().split(": ", 1) for line in metadata.strip().splitlines())
    system_message = {
        "role": "system",
        "content": (
            "You are a concise coding assistant. Use tools only when the user asks you to operate on files "
            "or use a tool. Use delegate_explorer for flowcharts and delegate_comparator for comparisons. "
            f"Available skill: {skill['name']} — {skill['description']} "
            f"Before using the skill, read the instructions via the read tool with path {SKILL_ID}."
        ),
    }
    session = Session(workspace.state_dir / "parent.jsonl")
    context = Context(system_message, session.load())
    registry = make_registry(workspace, provider)

    def emit(event_type, **data):
        render_event({"type": event_type, **data})

    return Runtime(
        context, provider, registry.schemas(), registry, Sandbox(ALLOWED_TOOLS), emit,
        session, workspace.state_dir / "run.json", 8, 2,
    )
