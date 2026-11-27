import json


# [V1.0 新增] 管理当前上下文中的消息
class Context:
    # 初始化：系统提示词 + 从 Session 恢复的历史消息
    def __init__(self, system_message, history):
        self.messages = [
            system_message,
            *history,
        ]

    # [V1.0 新增] 将新消息加入当前 Context
    def append(self, message):
        self.messages.append(message)

    # [V1.0 新增] 调用模型，把较早的消息压缩成摘要
    def summarize_messages(self, old_messages, provider):
        summary_messages = [
            {
                "role": "system",
                "content": (
                    "Summarize the earlier conversation concisely. "
                    "Preserve user facts, decisions, file changes, "
                    "tool results, and unfinished tasks."
                ),
            },
            {
                "role": "user",
                # 把旧消息列表转换为 JSON 字符串，再交给模型
                "content": json.dumps(old_messages, ensure_ascii=False),
            },
        ]

        # Provider 负责模型请求；Context 只取回摘要内容
        assistant_message = provider.call(summary_messages)
        return assistant_message["content"]

    # [V1.0 新增] 压缩旧消息，并保留最近几轮对话
    def compact(self, provider, max_messages, recent_turns):
        # 消息未超过阈值 → 不压缩
        if len(self.messages) <= max_messages:
            return 0

        # 每条 user 消息开启一轮，记录所有 user 消息的位置
        user_indexes = [
            index
            for index, message in enumerate(self.messages)
            if message["role"] == "user"
        ]

        # 用户轮数不足 → 没有需要压缩的更早对话
        if len(user_indexes) <= recent_turns:
            return 0

        # 从倒数第 recent_turns 条 user 消息开始保留
        split_index = user_indexes[-recent_turns]
        system_message = self.messages[0]  # 保留原系统提示词
        old_messages = self.messages[1:split_index]  # 需要压缩的旧消息
        recent_messages = self.messages[split_index:]  # 原样保留的近期消息

        # 调用模型生成摘要
        summary = self.summarize_messages(old_messages, provider)

        # 用系统提示词、摘要和近期消息重建 Context
        self.messages = [
            system_message,
            {
                "role": "system",
                "content": f"Summary of earlier conversation:\n{summary}",
            },
            *recent_messages,
        ]

        # 告诉调用方本次压缩了多少条消息
        return len(old_messages)
