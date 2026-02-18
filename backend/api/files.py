"""
文件操作 API
支持目录浏览、文件读取、文件写入
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import os
import mimetypes
from pathlib import Path
from typing import Optional, List

router = APIRouter()

# 允许浏览的根目录（安全限制）
# 设置为用户主目录，防止越权访问
import os
ALLOWED_BASE_DIRS = [os.path.expanduser("~")]  # 只允许访问用户主目录


def get_user_home() -> str:
    """获取用户主目录"""
    return os.path.expanduser("~")


class FileInfo(BaseModel):
    """文件信息模型"""
    name: str
    path: str
    is_dir: bool
    size: int
    modified: float
    extension: Optional[str] = None
    mime_type: Optional[str] = None


class DirectoryListing(BaseModel):
    """目录列表模型"""
    path: str
    parent: Optional[str]
    items: List[FileInfo]


class FileWriteRequest(BaseModel):
    """文件写入请求"""
    content: str


class PathRequest(BaseModel):
    """路径请求"""
    path: str


def is_path_allowed(path: str) -> bool:
    """检查路径是否允许访问"""
    if ALLOWED_BASE_DIRS is None:
        return True

    abs_path = os.path.abspath(path)
    for base_dir in ALLOWED_BASE_DIRS:
        if abs_path.startswith(os.path.abspath(base_dir)):
            return True
    return False


def get_file_info(path: str) -> FileInfo:
    """获取文件信息"""
    stat = os.stat(path)
    is_dir = os.path.isdir(path)

    # 获取扩展名和 MIME 类型
    extension = None
    mime_type = None
    if not is_dir:
        extension = os.path.splitext(path)[1].lower()
        mime_type, _ = mimetypes.guess_type(path)

    return FileInfo(
        name=os.path.basename(path),
        path=path,  # 返回绝对路径
        is_dir=is_dir,
        size=stat.st_size if not is_dir else 0,
        modified=stat.st_mtime,
        extension=extension,
        mime_type=mime_type
    )


@router.get("/list", response_model=DirectoryListing)
async def list_directory(
    path: str = Query("/", description="要列出的目录路径"),
    show_hidden: bool = Query(False, description="是否显示隐藏文件")
):
    """
    列出目录内容

    - **path**: 目录路径，默认为根目录
    - **show_hidden**: 是否显示隐藏文件（以 . 开头的文件）
    """
    # 展开 ~ 为用户目录
    path = os.path.expanduser(path)
    # 规范化路径
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        path = "/" + path

    # 安全检查
    if not is_path_allowed(path):
        raise HTTPException(status_code=403, detail="路径访问被拒绝")

    # 检查路径是否存在
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="路径不存在")

    # 检查是否为目录
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="不是有效的目录")

    try:
        items = []
        for item_name in os.listdir(path):
            # 跳过隐藏文件
            if not show_hidden and item_name.startswith('.'):
                continue

            item_path = os.path.join(path, item_name)
            try:
                items.append(get_file_info(item_path))
            except (PermissionError, OSError):
                # 跳过无权限访问的文件
                continue

        # 排序：目录在前，然后按名称排序
        items.sort(key=lambda x: (not x.is_dir, x.name.lower()))

        # 获取父目录路径（检查是否在允许范围内）
        parent = os.path.dirname(path)
        if parent and not is_path_allowed(parent):
            parent = None  # 不允许访问上级目录

        return DirectoryListing(
            path=path,
            parent=parent,
            items=items
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限访问该目录")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取目录失败: {str(e)}")


@router.get("/read")
async def read_file(
    path: str = Query(..., description="要读取的文件路径"),
    encoding: str = Query("utf-8", description="文件编码"),
    start_line: int = Query(0, description="起始行号（从0开始）"),
    line_count: int = Query(0, description="读取行数（0表示全部）")
):
    """
    读取文件内容

    - **path**: 文件路径
    - **encoding**: 文件编码，默认 UTF-8
    - **start_line**: 起始行号，用于大文件分页
    - **line_count**: 读取行数，0 表示读取全部
    """
    # 展开 ~ 为用户目录
    path = os.path.expanduser(path)
    # 规范化路径
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        path = "/" + path

    # 安全检查
    if not is_path_allowed(path):
        raise HTTPException(status_code=403, detail="路径访问被拒绝")

    # 检查文件是否存在
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查是否为文件
    if not os.path.isfile(path):
        raise HTTPException(status_code=400, detail="不是有效的文件")

    # 检查文件大小（限制大文件）
    file_size = os.path.getsize(path)
    max_size = 10 * 1024 * 1024  # 10MB
    if file_size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大（{file_size / 1024 / 1024:.2f}MB），超过限制（10MB）"
        )

    try:
        with open(path, 'r', encoding=encoding) as f:
            if start_line > 0 or line_count > 0:
                # 分页读取
                lines = []
                for i, line in enumerate(f):
                    if i < start_line:
                        continue
                    if line_count > 0 and i >= start_line + line_count:
                        break
                    lines.append(line)
                content = ''.join(lines)
                total_lines = i + 1 if 'i' in dir() else 0
            else:
                # 读取全部
                content = f.read()
                total_lines = content.count('\n') + 1

        # 获取文件信息
        file_info = get_file_info(path)

        return {
            "path": path,
            "content": content,
            "size": file_size,
            "lines": total_lines,
            "encoding": encoding,
            "mime_type": file_info.mime_type,
            "extension": file_info.extension
        }
    except UnicodeDecodeError:
        # 尝试其他编码
        alternative_encodings = ['gbk', 'gb2312', 'latin-1']
        for enc in alternative_encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    content = f.read()
                return {
                    "path": path,
                    "content": content,
                    "size": file_size,
                    "lines": content.count('\n') + 1,
                    "encoding": enc,
                    "mime_type": file_info.mime_type,
                    "extension": file_info.extension
                }
            except UnicodeDecodeError:
                continue
        raise HTTPException(status_code=400, detail="无法解码文件内容，可能是二进制文件")
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限读取该文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


@router.post("/write")
async def write_file(
    path: str = Query(..., description="要写入的文件路径"),
    request: FileWriteRequest = None
):
    """
    写入文件内容

    - **path**: 文件路径
    - **content**: 文件内容
    """
    # 展开 ~ 为用户目录
    path = os.path.expanduser(path)
    # 规范化路径
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        path = "/" + path

    # 安全检查
    if not is_path_allowed(path):
        raise HTTPException(status_code=403, detail="路径访问被拒绝")

    # 检查目录是否存在
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        raise HTTPException(status_code=400, detail="目录不存在")

    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(request.content)

        return {"success": True, "path": path, "size": len(request.content)}
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限写入该文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入文件失败: {str(e)}")


@router.get("/stat")
async def get_file_stat(path: str = Query(..., description="文件路径")):
    """
    获取文件详细信息
    """
    # 展开 ~ 为用户目录
    path = os.path.expanduser(path)
    # 规范化路径
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        path = "/" + path

    # 安全检查
    if not is_path_allowed(path):
        raise HTTPException(status_code=403, detail="路径访问被拒绝")

    # 检查路径是否存在
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="路径不存在")

    try:
        stat = os.stat(path)
        return {
            "path": path,
            "name": os.path.basename(path),
            "is_dir": os.path.isdir(path),
            "is_file": os.path.isfile(path),
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime,
            "mode": stat.st_mode
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限访问")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.post("/create")
async def create_file(request: PathRequest):
    """
    创建新文件

    - **path**: 文件路径
    """
    path = request.path
    # 展开 ~ 为用户目录
    path = os.path.expanduser(path)
    # 规范化路径
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        path = "/" + path

    # 安全检查
    if not is_path_allowed(path):
        raise HTTPException(status_code=403, detail="路径访问被拒绝")

    # 检查文件是否已存在
    if os.path.exists(path):
        raise HTTPException(status_code=400, detail="文件已存在")

    # 检查目录是否存在
    dir_path = os.path.dirname(path)
    if dir_path and not os.path.exists(dir_path):
        raise HTTPException(status_code=400, detail="目录不存在")

    try:
        # 创建空文件
        with open(path, 'w', encoding='utf-8') as f:
            f.write('')

        return {"success": True, "path": path}
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限创建文件")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建文件失败: {str(e)}")


@router.post("/mkdir")
async def create_directory(request: PathRequest):
    """
    创建新目录

    - **path**: 目录路径
    """
    path = request.path
    # 展开 ~ 为用户目录
    path = os.path.expanduser(path)
    # 规范化路径
    path = os.path.normpath(path)
    if not os.path.isabs(path):
        path = "/" + path

    # 安全检查
    if not is_path_allowed(path):
        raise HTTPException(status_code=403, detail="路径访问被拒绝")

    # 检查目录是否已存在
    if os.path.exists(path):
        raise HTTPException(status_code=400, detail="目录已存在")

    try:
        os.makedirs(path)

        return {"success": True, "path": path}
    except PermissionError:
        raise HTTPException(status_code=403, detail="无权限创建目录")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建目录失败: {str(e)}")
