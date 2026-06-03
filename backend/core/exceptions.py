"""统一异常处理.

所有 DRF API 异常和 Django Http404 被捕获后，统一包装为：
{
    "success": false,
    "data": null,
    "error": {"code": "ERROR_CODE", "message": "人类可读的错误描述"}
}
"""

from django.http import Http404
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def _build_error(code: str, message: str) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message},
    }


def unified_exception_handler(exc: Exception, context: dict) -> Response | None:
    """统一异常处理器.

    将 DRF 异常和 Django Http404 包装为统一格式。
    非预期的未处理异常不会被包装（便于调试）。
    """
    # 先走 DRF 默认处理，获取标准 Response
    response = drf_exception_handler(exc, context)

    if response is not None:
        # DRF 能识别的异常
        status_code = response.status_code
        detail = response.data

        # 提取 DRF 默认详情中的错误描述
        if isinstance(detail, dict):
            # 取第一个字段的第一条错误信息
            for key, value in detail.items():
                if isinstance(value, list):
                    message = str(value[0])
                else:
                    message = str(value)
                break
        elif isinstance(detail, list):
            message = str(detail[0])
        else:
            message = str(detail)

        # 根据状态码决定错误码
        error_code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            429: "TOO_MANY_REQUESTS",
        }
        code = error_code_map.get(status_code, "ERROR")

        return Response(
            _build_error(code, message),
            status=status_code,
        )

    # 单独处理 Http404（DRF 有时不在此列）
    if isinstance(exc, Http404):
        return Response(
            _build_error("NOT_FOUND", "请求的资源不存在"),
            status=404,
        )

    # 其他异常不包装，让 Django 默认处理
    return None
