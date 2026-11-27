import json
from pathlib import Path


# [V1.0 新增] 把main中的全局函数（load_session、add_message）封装成了一个对象，专门负责「管理会话历史」
class Session:
    # 初始化
    def __init__(self, path):
        self.path = Path(path)
        self.messages = []

    # 读档：从磁盘恢复
    def load(self):
        self.messages = []          # 先清空（防重复调用堆积）

        if not self.path.exists():  # 文件不存在 → 返回空列表
            return self.messages

        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():  # 非空行
                    self.messages.append(json.loads(line))

        return self.messages

    # 存档：写内存 + 写磁盘
    def append(self, message):
        self.messages.append(message)                                   # ← 写内存：直接加 message（Python 字典）

        self.path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")     # ← 写磁盘：把字典转成 JSON 字符串写进去
