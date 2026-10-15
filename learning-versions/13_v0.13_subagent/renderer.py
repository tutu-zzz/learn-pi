"""
举例：用户说「读 README 并总结」
---------------------------------------------
事件流：
model_start          → 打印 "Answer: "
model_delta "我来读"  → 屏幕: Answer: 我来读
model_delta "一下"    → 屏幕: Answer: 我来读一下
model_end            → 换行
tool_start           → 打印 "调用工具..."
tool_end             → 打印 "工具执行结果..."
model_start          → 打印 "Answer: "   ← 又一轮！
model_delta "这个项目" → 屏幕: Answer: 这个项目
model_delta "是..."   → 屏幕: Answer: 这个项目是...
model_end            → 换行
agent_end            → 打印 "Answer: 这个项目是..."  ← 最终答案
---------------------------------------------
屏幕最终显示：
Answer: 我来读一下
调用工具 Tool Call: read_file, 参数: {...}
工具执行结果 Tool Result:
# learn-pi
...
Answer: 这个项目是...
Answer: 这个项目是...      ← 最后这行，是 agent_end 打的    
"""

# [V0.11 新增] 将 Runtime 事件显示到终端
def render_event(event):
    event_type = event["type"]
    
    if event_type == "model_start":
        print("Answer: ", end="", flush=True)
        
    elif event_type == "model_delta":               # model_delta 是「正在生成的回答内容」的逐段推送
        print(event["delta"], end="", flush=True)
        
    elif event_type == "model_end":
        print()
    
    elif event_type == "tool_start":
        print(
            f"调用工具 Tool Call: {event['name']}, "
            f"参数: {event['arguments']}"
        )
        
    elif event_type == "tool_end":
        print(
            f"工具执行结果 Tool Result:\n"
            f"{event['result']}"
        )
        
    elif event_type == "agent_end":
        print(f"Answer: {event['answer']}")