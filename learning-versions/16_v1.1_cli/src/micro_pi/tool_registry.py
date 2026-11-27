# [V1.0 新增] 管理工具的注册、查找和模型可见的 Schema
class ToolRegistry:
    # 初始化：接收已有工具，创建自己的注册表
    def __init__(self, tools):
        self.tools = dict(tools)

    # [V1.0 新增] 注册工具，供内置工具或 Extension 使用
    def register(self, name, description, parameters, execute):
        self.tools[name] = {
            "description": description,
            "parameters": parameters,
            "execute": execute,
        }

    # [V1.0 新增] 根据名称查找工具
    def get(self, name):
        return self.tools.get(name)

    # [V1.0 新增] 生成发给模型的 Tool Schema
    def schemas(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            for name, tool in self.tools.items()
        ]
