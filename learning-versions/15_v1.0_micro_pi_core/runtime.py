import json

# [V1.0 修改] Runtime 读取并保存 Checkpoint
from durable import load_checkpoint, save_checkpoint

'''
Runtime 对象
  ├── context / provider     模型与上下文
  ├── tools / registry       工具信息
  ├── sandbox                工具权限
  ├── emit / add_message     事件与消息
  └── checkpoint / 配置      运行状态与压缩规则
'''
# [V1.0 新增] 保存 Agent Runtime 运行时需要的对象和配置
class Runtime:
    def __init__(
        self,
        context,
        provider,
        tools,
        tool_registry,
        sandbox,
        emit,
        session,
        checkpoint_path,
        max_context_messages,
        recent_turns,
    ):
        # 模型与上下文
        self.context = context
        self.provider = provider

        # 工具定义、注册表和权限检查
        self.tools = tools
        self.tool_registry = tool_registry
        self.sandbox = sandbox

        # 事件、消息保存和运行状态
        self.emit = emit
        self.session = session
        self.checkpoint_path = checkpoint_path

        # Context 压缩配置
        self.max_context_messages = max_context_messages
        self.recent_turns = recent_turns

    # [V1.0 新增] 将消息分别保存到 Session 和当前 Context
    def add_message(self, message):
        self.session.append(message)  # 保存完整历史到磁盘
        self.context.append(message)  # 加入当前模型上下文


    # [V1.0 新增] 读取需要恢复的任务状态
    def load_pending_run(self):
        checkpoint = load_checkpoint(self.checkpoint_path)
        if checkpoint and checkpoint.get("status") in ("RUNNING", "WAITING_TOOL"):
            return checkpoint
        return None

    # [V1.0 新增] 开始新任务：保存用户消息并记录运行状态
    def start_run(self, user_message):
        self.add_message(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # 新任务开始，保存 Checkpoint
        save_checkpoint(
            self.checkpoint_path,
            "RUNNING",
        )

        # 新任务没有待执行的 Tool Call
        self.run_agent_loop(None)


    # [V1.0 修改] 使用 Runtime 保存的依赖执行一次 Agent 任务
    def run_agent_loop(self, tool_calls):
        # Agent Loop：持续调用模型、执行工具，直到任务完成
        while True:
            # [V0.14 修改] 恢复时已有 Tool Call，不再重复调用模型
            if tool_calls is None:

                # [V1.0 修改] 检查并压缩 Context
                compacted_count = self.context.compact(
                    self.provider,
                    self.max_context_messages,
                    self.recent_turns,
                )

                # [V1.0 修改] 压缩后发送事件，由 Renderer 显示
                if compacted_count:
                    self.emit(
                        "context_compacted",
                        count=compacted_count,
                    )

                # [V1.0 修改] 使用 Runtime 保存的 Provider 和 Context
                assistant_message = self.provider.call(
                    self.context.messages,
                    self.tools,
                )
                self.add_message(assistant_message)

                tool_calls = assistant_message.get("tool_calls")

                # 没有工具调用 → 保存完成状态并结束本次任务
                if not tool_calls:
                    save_checkpoint(
                        self.checkpoint_path,
                        "SUCCEEDED",
                    )

                    self.emit(
                        "agent_end",
                        answer=assistant_message["content"],
                    )
                    break

                # [V0.14 新增] 保存待执行的工具调用
                save_checkpoint(
                    self.checkpoint_path,
                    "WAITING_TOOL",
                    tool_calls,
                )

            # 执行本轮所有工具调用
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_arguments = json.loads(
                    tool_call["function"]["arguments"]
                )

                # [V1.0 修改] 从 Runtime 保存的 Registry 查找工具
                tool = self.tool_registry.get(tool_name)
                if not tool:
                    raise RuntimeError(f"未知工具: {tool_name}")

                self.emit(
                    "tool_start",
                    name=tool_name,
                    arguments=tool_arguments,
                )

                # 先检查 Sandbox 权限，再执行工具
                try:
                    self.sandbox.check(tool_name)
                    tool_result = tool["execute"](**tool_arguments)
                except Exception as e:
                    tool_result = f"Error: {e}"

                self.emit(
                    "tool_end",
                    result=tool_result,
                )

                # 保存工具结果，让模型在下一轮读取
                self.add_message(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result,
                    }
                )

            # 工具执行完毕 → 更新状态，下一轮继续调用模型
            save_checkpoint(
                self.checkpoint_path,
                "RUNNING",
            )
            tool_calls = None
