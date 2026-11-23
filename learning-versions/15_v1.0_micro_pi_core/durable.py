import json


# [V0.14 新增] 存档：把当前状态写进文件，保存当前执行位置
def save_checkpoint(path, status, tool_calls=None):
    checkpoint = {
        "status": status,
        "tool_calls": tool_calls or [],
    }
    
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=4),
        encoding="utf-8",
        )
    
    
# [V0.14 新增] 读档：从文件恢复状态，读取上次保存的执行位置
def load_checkpoint(path):
    if not path.exists():
        return None
    
    return json.loads(path.read_text(encoding="utf-8"))