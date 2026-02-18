# Claude Remote 项目说明

## 项目结构

```
claude_code远程/
├── frontend/          # Vue 3 前端
├── backend/           # FastAPI 后端
│   ├── services/
│   │   ├── terminal_service.py  # 终端服务抽象接口
│   │   └── tmux_service.py      # Linux tmux 实现
│   └── platform_utils.py        # 平台检测工具
└── CLAUDE.md          # 本文档
```

## 环境要求

- **Linux** (仅支持 Linux)
- Node.js 18+
- Python 3.10+
- tmux (安装: `sudo apt install tmux`)

## 启动方式

### 启动后端

```bash
cd /path/to/claude_code远程/backend
pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 启动前端

```bash
cd /path/to/claude_code远程/frontend
npm run dev
```

## 访问地址

- 本机访问: http://localhost:3000
- 局域网访问: http://<服务器IP>:3000

## 后端架构

### 终端服务

后端使用 tmux 管理终端会话：

```
TerminalService (抽象接口)
    └── TmuxService (Linux tmux 实现)
```

### 使用示例

```python
from platform_utils import get_terminal_service

terminal = get_terminal_service()
terminal.create_session("session_name", "/work/dir", "claude")
```

## 终端锁定功能

- 锁定后：禁止键盘输入，防止误触，但可以滚动查看终端
- 使用 xterm.js 的 `readOnly` 模式实现
