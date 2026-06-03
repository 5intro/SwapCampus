"""统一分页配置.

API 返回格式：
{
    "success": true,
    "data": [...],
    "error": null,
    "pagination": { "page": 1, "page_size": 20, "total": 150 }
}
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """标准分页器，配合 core.exceptions.unified_exception_handler 使用."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response(
            {
                "success": True,
                "data": data,
                "error": None,
                "pagination": {
                    "page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                    "total": self.page.paginator.count,
                },
            }
        )
