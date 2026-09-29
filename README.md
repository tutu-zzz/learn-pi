# learn-pi

通过亲手实现一个极简、透明、终端原生的 `micro-pi`，逐步理解 Agent 的核心机制。

## 当前阶段

`V0.1 — 第一次 LLM 调用`

当前只关注一条最小链路：

```text
Terminal Input
    → LLM Request
    → LLM Response
    → Terminal Output
```

暂不引入 Tool、Agent Loop、Session、Skill、Sandbox 等后续能力。

## 项目结构

```text
learn-pi/
├── .env.example
├── .gitignore
├── docs/
│   ├── learn-pi_-_micro-pi_PRD.md
│   └── 进度.md
├── requirements.txt
├── src/
│   └── micro_pi/
│       ├── __init__.py
│       └── main.py
└── README.md
```

`src/micro_pi/` 中的代码文件有意保持空白，由学习者在每个阶段亲手完成。

真实 API Key 只保存在本地环境中，不写入源码；`.env.example` 只描述配置名称，不包含密钥。

## Python 环境

项目使用 Miniforge 管理的 Conda 环境：

```powershell
conda activate learn-pi
python src/micro_pi/main.py
```

环境位置为 `D:\miniforge3\conda-env\learn-pi`，项目依赖由 `requirements.txt` 管理。
