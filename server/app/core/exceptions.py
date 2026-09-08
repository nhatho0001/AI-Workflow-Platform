# app/core/exceptions.py

from fastapi import HTTPException, status
from typing import Any, Optional


class NotFoundException(HTTPException):
    """
    Raise khi resource không tồn tại trong DB.
    Tự động map sang HTTP 404.
    """
    def __init__(
        self,
        detail: Any = "Resource not found",
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
        )


class ForbiddenException(HTTPException):
    """
    Raise khi user không có quyền truy cập resource.
    Tự động map sang HTTP 403.
    """
    def __init__(
        self,
        detail: Any = "Access denied",
        headers: Optional[dict[str, str]] = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
        )