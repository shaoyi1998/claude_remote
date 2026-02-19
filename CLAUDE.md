# Claude Remote 项目说明

## 项目简介

Claude Remote 是一个 Claude Code 远程任务管理工具，让你可以通过浏览器远程管理和控制 Claude Code 终端会话。

## 项目结构

```
claude_remote/
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   ├── components/         # 通用组件
│   │   ├── stores/             # 状态管理
│   │   ├── api.js              # API 配置
│   │   └── router.js           # 路由配置
│   └── package.json
│
├── backend/                     # FastAPI 后端
│   ├── api/                    # API 路由
│   │   ├── auth.py            # 认证接口
│   │   ├── tasks.py           # 任务管理
│   │   ├── users.py           # 用户管理
│   │   ├── files.py           # 文件操作
│   │   └── proxy.py           # 反向代理
│   ├── services/              # 业务服务
│   │   ├── auth.py            # 认证服务
│   │   ├── database.py        # 数据库服务
│   │   ├── terminal_service.py # 终端抽象接口
│   │   └── tmux_service.py    # tmux 实现
│   ├── models/                 # 数据模型
│   │   ├── user.py            # 用户模型
│   │   ├── task.py            # 任务模型
│   │   └── user_config.py     # 用户配置
│   ├── config.py              # 配置管理
│   ├── main.py                # 应用入口
│   └── requirements.txt
│
├── CLAUDE.md                   # 本文档
├── 启动.md                     # 启动指南
└── README.md                   # 项目说明
```

## 环境要求

- **操作系统**: Linux（推荐 Ubuntu 22.04）或 WSL2
- **Node.js**: 18+
- **Python**: 3.10+
- **tmux**: 必需（`sudo apt install tmux`）

## 核心功能

### 1. 远程终端
- 基于 xterm.js 的完整终端模拟
- 支持实时 WebSocket 通信
- 终端锁定/解锁功能

### 2. 任务管理
- 创建、恢复、删除 Claude Code 任务
- 任务状态监控（运行中/已停止/错误）
- 任务配置（权限跳过、队友模式）

### 3. 快捷键系统
- 自定义命令按钮
- 自定义快捷键（支持 Ctrl/Shift/Alt 组合）
- 云端同步配置

### 4. 文件管理
- 浏览工作目录
- 查看文件内容
- 支持代码高亮

### 5. 反向代理
- 访问本地其他开发服务器
- 支持 HTTP 和 WebSocket

## 后端架构

### 终端服务

```
TerminalService (抽象基类)
    └── TmuxService (Linux tmux 实现)
```

使用示例：
```python
from platform_utils import get_terminal_service

terminal = get_terminal_service()
terminal.create_session("session_name", "/work/dir", "claude")
terminal.send_keys("session_name", "C-c")  # 发送 Ctrl+C
output = terminal.get_output("session_name")
```

### API 认证

所有 API（除了登录和初始化）都需要 JWT Token 认证：

```python
# 请求头
Authorization: Bearer <token>
```

### WebSocket

WebSocket 端点用于实时终端输出：

```
ws://host:port/ws/tasks/{task_id}?token=<jwt_token>
```

消息格式：
```json
{"type": "output", "data": "终端内容", "append": true}
{"type": "resize", "cols": 80, "rows": 24}
{"type": "input", "data": "用户输入"}
```

## 前端架构

### 技术栈
- Vue 3 + Composition API
- Vue Router
- xterm.js + xterm-addon-fit
- 原生 CSS（CSS Variables）

### 状态管理
- 用户配置：localStorage + 云端同步
- 终端状态：组件内 ref
- 快捷键配置：`stores/shortcuts.js`

### 移动端适配
- 响应式布局
- 触摸优化的快捷键面板
- 终端锁定模式（防止误触）

## 配置说明

### 环境变量

```ini
# JWT 密钥（默认自动生成，如需固定密钥请设置）
# SECRET_KEY=your-secret-key

# Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# 登录安全配置
LOGIN_MAX_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=1440

# 数据库路径
DATABASE_URL=sqlite:///./claude_remote.db

# CORS 来源
CORS_ORIGINS=*

# tmux 会话前缀
TMUX_SESSION_PREFIX=claude_

# Claude Code 命令
CLAUDE_COMMAND=claude
```

## 开发指南

### 添加新的 API 端点

1. 在 `backend/api/` 创建或编辑路由文件
2. 在 `backend/main.py` 注册路由
3. 在 `frontend/src/api.js` 添加请求方法

### 添加新的终端命令

1. 在 `backend/services/terminal_service.py` 添加方法
2. 在 `TmuxService` 中实现具体逻辑
3. 在 `api/tasks.py` 添加对应的 API

### 修改快捷键

编辑 `frontend/src/stores/shortcuts.js`:
- `defaultShortcuts.commands`: 自定义命令
- `defaultShortcuts.shortcuts`: 自定义快捷键

## 安全注意事项

1. **SECRET_KEY 默认自动生成** - 每次重启会生成新密钥，如需保持会话有效请手动设置
2. 默认管理员密码登录后立即修改
3. 生产环境设置 CORS_ORIGINS 为具体域名
4. 建议使用 HTTPS
5. 数据库文件不要提交到版本控制
6. 内置登录防爆破保护，连续 5 次失败锁定 IP 24 小时
