# Claude Remote 部署指南

## 项目简介

Claude Remote 是一个远程控制 Claude Code 终端会话的 Web 应用。

- **前端**：Vue 3 + Vite
- **后端**：FastAPI + tmux
- **终端**：xterm.js

## 环境要求

- Linux 服务器（需要 tmux）
- Python 3.10+
- Node.js 18+（仅打包前端时需要）

## 快速部署

### 1. 后端部署

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务（监听所有网卡）
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. 前端部署

**方式一：直接使用 Vite 开发服务器**

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

**方式二：打包静态文件（推荐生产环境）**

```bash
cd frontend
npm install
npm run build

# 生成的文件在 dist/ 目录
# 使用 nginx 或其他静态服务器托管
```

**Nginx 配置示例：**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

## 默认账号

- 用户名：`admin`
- 密码：`admin123`

首次登录后请修改密码。

## 项目结构

```
claude_code远程/
├── frontend/           # Vue 3 前端
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── api.js      # API 配置
│   │   └── router.js   # 路由配置
│   └── package.json
├── backend/            # FastAPI 后端
│   ├── api/            # API 路由
│   ├── services/       # 服务层
│   ├── models/         # 数据模型
│   └── main.py         # 入口文件
└── DEPLOY.md           # 本文档
```

## 常用命令

### 后端

```bash
# 启动后端
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# 后台运行（使用 nohup）
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

### 前端

```bash
# 开发模式
npm run dev -- --host 0.0.0.0

# 打包生产版本
npm run build
```

## 注意事项

1. **tmux 依赖**：后端必须运行在支持 tmux 的 Linux 环境中
2. **网络访问**：确保服务器防火墙开放 8000（后端）和 3000/80（前端）端口
3. **WebSocket**：后端使用 WebSocket 实时传输终端输出，确保代理服务器支持 WebSocket

## 功能说明

### 终端锁定

在任务详情页点击"锁定"按钮可以锁定终端，防止误触弹出输入法。锁定后：
- 点击终端不会弹出输入法
- 仍可以滑动查看终端内容
- 显示锁形图标表示锁定状态

### 快捷键面板

提供常用快捷键按钮：
- Esc、方向键、Enter
- 退格（支持长按加速）
- Shift + 方向键
- 底部滚动
- 快捷命令（横屏显示）

## 故障排除

### 无法连接后端

1. 检查后端是否启动：`curl http://localhost:8000/api/tasks`
2. 检查防火墙：`sudo ufw status`
3. 检查端口监听：`netstat -tlnp | grep 8000`

### WebSocket 连接失败

1. 确保代理服务器配置了 WebSocket 支持
2. 检查浏览器控制台错误信息
3. 确认后端日志没有报错

### 终端不显示内容

1. 检查任务状态是否为 "running"
2. 确认 tmux 会话存在：`tmux ls`
3. 检查后端 WebSocket 连接状态
