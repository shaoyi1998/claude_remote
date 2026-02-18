"""
反向代理 API - 将请求代理到本地端口
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, Response
import httpx

from services.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proxy", tags=["代理"])

# HTTP 客户端配置
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0, connect=10.0),
    follow_redirects=False,  # 不自动跟随重定向，我们自己处理
)

# 允许代理的端口范围（安全限制）
ALLOWED_PORT_MIN = 1024  # 不允许特权端口
ALLOWED_PORT_MAX = 65535

# 需要转发的请求头（排除 hop-by-hop 头）
HOP_BY_HOP_HEADERS = {
    'connection', 'keep-alive', 'proxy-authenticate',
    'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
    'upgrade', 'host'
}


def validate_port(port: int) -> None:
    """验证端口号是否在允许范围内"""
    if not (ALLOWED_PORT_MIN <= port <= ALLOWED_PORT_MAX):
        raise HTTPException(status_code=400, detail=f"端口号必须在 {ALLOWED_PORT_MIN}-{ALLOWED_PORT_MAX} 范围内")


async def verify_token_dependency(token: Optional[str] = Query(None)) -> dict:
    """验证 token 的依赖项"""
    if not token:
        raise HTTPException(status_code=401, detail="缺少认证 token")
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="无效的 token")
    return {"user": user}


@router.api_route(
    "/{port}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    summary="代理 HTTP 请求"
)
async def proxy_http(
    port: int,
    path: str,
    request: Request,
    _: dict = Depends(verify_token_dependency)
):
    """
    将 HTTP 请求代理到 localhost:port/path

    用法: GET /proxy/8080/some/path?token=xxx
    """
    validate_port(port)

    # 构建目标 URL
    target_url = f"http://127.0.0.1:{port}/{path}"
    if request.url.query:
        # 重新构建查询字符串（排除 token 参数）
        query_params = dict(request.query_params)
        query_params.pop('token', None)
        if query_params:
            target_url += "?" + "&".join(f"{k}={v}" for k, v in query_params.items())

    # 准备转发的请求头
    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in HOP_BY_HOP_HEADERS:
            headers[key] = value

    # 修改 Host 头为目标服务器
    headers['host'] = f'127.0.0.1:{port}'

    # 获取请求体
    body = await request.body()

    logger.info(f"代理请求: {request.method} {target_url}")

    try:
        # 发送请求到目标服务器
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )

        # 准备响应头（排除 hop-by-hop 头）
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in HOP_BY_HOP_HEADERS:
                response_headers[key] = value

        # 处理重定向（修改 Location 头）
        if 'location' in response.headers:
            location = response.headers['location']
            # 如果是相对路径或指向同一主机，需要修改为代理路径
            if location.startswith('/') or location.startswith(f'http://127.0.0.1:{port}'):
                # 提取路径部分
                if location.startswith('http'):
                    from urllib.parse import urlparse
                    parsed = urlparse(location)
                    new_path = parsed.path
                    if parsed.query:
                        new_path += f"?{parsed.query}"
                else:
                    new_path = location
                # 重写为代理路径
                token = request.query_params.get('token', '')
                response_headers['location'] = f"/proxy/{port}{new_path}?token={token}"

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=response_headers,
            media_type=response.headers.get('content-type')
        )

    except httpx.ConnectError:
        logger.warning(f"无法连接到目标服务: {target_url}")
        raise HTTPException(status_code=502, detail=f"无法连接到本地端口 {port}")
    except httpx.TimeoutException:
        logger.warning(f"连接超时: {target_url}")
        raise HTTPException(status_code=504, detail="连接超时")
    except Exception as e:
        logger.error(f"代理请求失败: {e}")
        raise HTTPException(status_code=500, detail=f"代理请求失败: {str(e)}")


@router.websocket("/ws/{port}/{path:path}")
async def proxy_websocket(
    websocket: WebSocket,
    port: int,
    path: str,
    token: str = Query(...)
):
    """
    代理 WebSocket 连接到 localhost:port/path

    用法: ws://host:8000/proxy/ws/8080/some/path?token=xxx
    """
    validate_port(port)

    # 验证 token
    user = verify_token(token)
    if not user:
        await websocket.close(code=4001, reason="无效的 token")
        return

    await websocket.accept()

    # 构建目标 WebSocket URL
    target_url = f"ws://127.0.0.1:{port}/{path}"
    if websocket.query_params:
        # 重新构建查询字符串（排除 token 参数）
        query_params = dict(websocket.query_params)
        query_params.pop('token', None)
        if query_params:
            target_url += "?" + "&".join(f"{k}={v}" for k, v in query_params.items())

    logger.info(f"代理 WebSocket: {target_url}")

    # 使用 httpx 的 WebSocket 客户端（如果支持）或使用 websockets 库
    try:
        import websockets
    except ImportError:
        await websocket.close(code=1011, reason="服务器缺少 websockets 库")
        return

    try:
        async with websockets.connect(target_url) as target_ws:
            logger.info(f"WebSocket 已连接到: {target_url}")

            async def forward_to_target():
                """从客户端转发消息到目标"""
                try:
                    while True:
                        data = await websocket.receive()
                        if 'text' in data:
                            await target_ws.send(data['text'])
                        elif 'bytes' in data:
                            await target_ws.send(data['bytes'])
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logger.debug(f"forward_to_target 结束: {e}")

            async def forward_to_client():
                """从目标转发消息到客户端"""
                try:
                    async for message in target_ws:
                        if isinstance(message, str):
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except Exception as e:
                    logger.debug(f"forward_to_client 结束: {e}")

            # 并行运行两个转发任务
            import asyncio
            await asyncio.gather(
                forward_to_target(),
                forward_to_client(),
                return_exceptions=True
            )

    except ConnectionRefusedError:
        logger.warning(f"无法连接到目标 WebSocket: {target_url}")
        await websocket.close(code=502, reason=f"无法连接到本地端口 {port}")
    except Exception as e:
        logger.error(f"WebSocket 代理错误: {e}")
        await websocket.close(code=1011, reason=str(e))


@router.get("/", summary="代理入口页面")
async def proxy_index(
    _: dict = Depends(verify_token_dependency)
):
    """返回简单的代理使用说明"""
    return {
        "message": "Claude Remote 反向代理",
        "usage": {
            "http": "/proxy/{port}/{path}?token=xxx",
            "websocket": "/proxy/ws/{port}/{path}?token=xxx"
        },
        "example": "/proxy/8080/index.html?token=xxx"
    }
