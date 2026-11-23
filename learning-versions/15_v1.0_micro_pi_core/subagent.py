import json

# [V0.13 新增] 同时保存 Child 的内存消息和 Session
def add_message(messages, session_path, message):
    messages.append(message)
    
    session_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(session_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(message, ensure_ascii=False) + "\n")



# [V0.13 新增] 使用独立 Messages 运行 Subagent，不同 Child 使用不同职责提示词
def run_subagent(task, system_message, call_model, read_file, tools, session_path):
    messages = [
        {
            "role": "system",
            "content": system_message,
        },
    ]
    
    
    add_message(
        messages,
        session_path,
        {
            "role": "user",
            "content": task,
        },
    )
    
    
    while True:
        assistant_message = call_model(messages, tools)
        add_message(
            messages,
            session_path,
            assistant_message,
        )
        
        tool_calls = assistant_message.get("tool_calls")
        
        if not tool_calls:
            return assistant_message["content"]
        
        
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_arguments = json.loads(tool_call["function"]["arguments"])
            
            # Subagent 仅支持 read 工具
            if tool_name != "read":
                tool_result = (
                    f"Error: Subagent cannot use tool: {tool_name} "
                )
            else:
                try:
                    tool_result = read_file(**tool_arguments)
                except Exception as e:
                    tool_result = f"Error: {e}"
            
            
            add_message(
                messages,
                session_path,
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": tool_result,
                },
            )