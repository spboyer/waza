"""JSON-RPC 2.0 protocol implementation."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ErrorCode(IntEnum):
    """JSON-RPC 2.0 error codes."""

    # Standard JSON-RPC errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Custom application errors
    EVAL_NOT_FOUND = -32000
    VALIDATION_FAILED = -32001
    RUN_FAILED = -32002


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request."""

    jsonrpc: str = Field(default="2.0", pattern="^2\\.0$")
    method: str
    params: dict[str, Any] | list[Any] | None = None
    id: str | int | None = None

    @field_validator("jsonrpc")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate JSON-RPC version."""
        if v != "2.0":
            raise ValueError("jsonrpc must be '2.0'")
        return v

    @property
    def is_notification(self) -> bool:
        """Check if this is a notification (no id)."""
        return self.id is None


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 error object."""

    code: int
    message: str
    data: Any | None = None

    @classmethod
    def parse_error(cls, data: Any | None = None) -> "JSONRPCError":
        """Create a parse error."""
        return cls(
            code=ErrorCode.PARSE_ERROR,
            message="Parse error",
            data=data,
        )

    @classmethod
    def invalid_request(cls, data: Any | None = None) -> "JSONRPCError":
        """Create an invalid request error."""
        return cls(
            code=ErrorCode.INVALID_REQUEST,
            message="Invalid request",
            data=data,
        )

    @classmethod
    def method_not_found(cls, method: str) -> "JSONRPCError":
        """Create a method not found error."""
        return cls(
            code=ErrorCode.METHOD_NOT_FOUND,
            message="Method not found",
            data={"method": method},
        )

    @classmethod
    def invalid_params(cls, message: str) -> "JSONRPCError":
        """Create an invalid params error."""
        return cls(
            code=ErrorCode.INVALID_PARAMS,
            message=f"Invalid params: {message}",
        )

    @classmethod
    def internal_error(cls, message: str) -> "JSONRPCError":
        """Create an internal error."""
        return cls(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Internal error: {message}",
        )

    @classmethod
    def eval_not_found(cls, path: str) -> "JSONRPCError":
        """Create an eval not found error."""
        return cls(
            code=ErrorCode.EVAL_NOT_FOUND,
            message="Eval not found",
            data={"path": path},
        )

    @classmethod
    def validation_failed(cls, errors: list[str]) -> "JSONRPCError":
        """Create a validation failed error."""
        return cls(
            code=ErrorCode.VALIDATION_FAILED,
            message="Validation failed",
            data={"errors": errors},
        )

    @classmethod
    def run_failed(cls, message: str) -> "JSONRPCError":
        """Create a run failed error."""
        return cls(
            code=ErrorCode.RUN_FAILED,
            message=f"Run failed: {message}",
        )


class JSONRPCException(Exception):
    """Exception that wraps a JSON-RPC error for raising in handlers."""

    def __init__(self, error: JSONRPCError):
        """Initialize exception with error object.
        
        Args:
            error: The JSON-RPC error object.
        """
        self.error = error
        super().__init__(error.message)


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response."""

    jsonrpc: str = Field(default="2.0", pattern="^2\\.0$")
    id: str | int | None
    result: Any | None = None
    error: JSONRPCError | None = None

    @field_validator("jsonrpc")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate JSON-RPC version."""
        if v != "2.0":
            raise ValueError("jsonrpc must be '2.0'")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate that exactly one of result or error is set."""
        if self.result is not None and self.error is not None:
            raise ValueError("Response cannot have both result and error")
        if self.result is None and self.error is None:
            raise ValueError("Response must have either result or error")

    @classmethod
    def success(cls, id: str | int | None, result: Any) -> JSONRPCResponse:
        """Create a success response."""
        return cls(id=id, result=result)

    @classmethod
    def error_response(cls, id: str | int | None, error: JSONRPCError) -> JSONRPCResponse:
        """Create an error response."""
        return cls(id=id, error=error)


class JSONRPCNotification(BaseModel):
    """JSON-RPC 2.0 notification (server → client)."""

    jsonrpc: str = Field(default="2.0", pattern="^2\\.0$")
    method: str
    params: dict[str, Any] | list[Any] | None = None

    @field_validator("jsonrpc")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate JSON-RPC version."""
        if v != "2.0":
            raise ValueError("jsonrpc must be '2.0'")
        return v
