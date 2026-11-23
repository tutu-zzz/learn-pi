# [V0.12 新增] 工具权限边界，用白名单限制「哪些工具允许执行」
class Sandbox:
    def __init__(self, allowed_tools):          # 传入允许的工具
        self.allowed_tools = allowed_tools

    def check(self, tool_name):                 # 不在名单就拒绝
        if tool_name not in self.allowed_tools:
            raise PermissionError(f"Sandbox blocked tool: {tool_name}")