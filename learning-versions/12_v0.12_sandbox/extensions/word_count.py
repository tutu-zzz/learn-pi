# [V0.10 新增] Extension 提供的工具函数
def word_count(text):
    return f"Word count: {len(text.split())}"


# [V0.10 新增] Extension 入口
def setup(pi):
    pi.register_tool(
        name="word_count",
        description="Count the number of words in the given text.",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to count words in."
                }
            },
            "required": ["text"]
        },
        execute=word_count,
    )