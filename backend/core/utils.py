"""工具函数."""

import hashlib
import uuid
from io import BytesIO
from typing import Any

from django.core.files.base import ContentFile
from PIL import Image


def generate_uuid4() -> uuid.UUID:
    """生成 UUID4，封装以便后续可能的替换（如 UUID7）。"""
    return uuid.uuid4()


def compress_image(
    image_file: Any,
    max_width: int = 1920,
    quality: int = 85,
    fmt: str = "JPEG",
) -> ContentFile:
    """压缩上传的图片.

    Args:
        image_file: Django UploadedFile 对象
        max_width: 最大宽度（像素），等比缩放
        quality: JPEG 质量（1-100）
        fmt: 输出格式

    Returns:
        压缩后的 ContentFile 对象，可直接用于 Django FileField
    """
    img = Image.open(image_file)
    # 转 RGB（处理 RGBA/PNG）
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    # 等比缩放
    width_percent = max_width / float(img.size[0])
    if width_percent < 1.0:
        new_height = int(float(img.size[1]) * width_percent)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    # 写入内存
    output = BytesIO()
    img.save(output, format=fmt, quality=quality)
    ext = "jpg" if fmt.upper() == "JPEG" else fmt.lower()
    name = getattr(image_file, "name", f"image.{ext}")
    # 确保文件扩展名匹配输出格式
    if not name.lower().endswith(f".{ext}"):
        name = f"{name.rsplit('.', 1)[0]}.{ext}" if "." in name else f"{name}.{ext}"
    return ContentFile(output.getvalue(), name=name)


def file_md5(file_obj) -> str:
    """计算上传文件的 MD5 值，用于去重."""
    md5 = hashlib.md5()
    for chunk in file_obj.chunks():
        md5.update(chunk)
    return md5.hexdigest()


def build_success_response(data: Any) -> dict:
    """构建统一的成功响应体（供非 DRF View 使用）."""
    return {"success": True, "data": data, "error": None}


def build_error_response(code: str, message: str) -> dict:
    """构建统一的错误响应体."""
    return {"success": False, "data": None, "error": {"code": code, "message": message}}
