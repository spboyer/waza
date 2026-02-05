"""Tests for JSON-RPC protocol implementation."""

import pytest
from pydantic import ValidationError

from waza.jsonrpc.protocol import (
    ErrorCode,
    JSONRPCError,
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
)


class TestJSONRPCRequest:
    """Tests for JSONRPCRequest."""

    def test_valid_request(self):
        """Test creating a valid request."""
        request = JSONRPCRequest(
            jsonrpc="2.0",
            method="eval.run",
            params={"path": "/path/to/eval.yaml"},
            id=1,
        )
        assert request.jsonrpc == "2.0"
        assert request.method == "eval.run"
        assert request.params == {"path": "/path/to/eval.yaml"}
        assert request.id == 1
        assert not request.is_notification

    def test_request_with_string_id(self):
        """Test request with string ID."""
        request = JSONRPCRequest(
            method="eval.list",
            params={"directory": "/path"},
            id="req-123",
        )
        assert request.id == "req-123"

    def test_notification(self):
        """Test notification (no id)."""
        notification = JSONRPCRequest(
            method="eval.cancel",
            params={"runId": "abc"},
        )
        assert notification.id is None
        assert notification.is_notification

    def test_invalid_version(self):
        """Test invalid JSON-RPC version."""
        with pytest.raises(ValidationError):
            JSONRPCRequest(
                jsonrpc="1.0",
                method="test",
                id=1,
            )

    def test_missing_method(self):
        """Test missing method."""
        with pytest.raises(ValidationError):
            JSONRPCRequest(
                jsonrpc="2.0",
                id=1,
            )


class TestJSONRPCResponse:
    """Tests for JSONRPCResponse."""

    def test_success_response(self):
        """Test creating a success response."""
        response = JSONRPCResponse.success(
            id=1,
            result={"runId": "abc123", "status": "running"},
        )
        assert response.jsonrpc == "2.0"
        assert response.id == 1
        assert response.result == {"runId": "abc123", "status": "running"}
        assert response.error is None

    def test_error_response(self):
        """Test creating an error response."""
        error = JSONRPCError(
            code=ErrorCode.METHOD_NOT_FOUND,
            message="Method not found",
        )
        response = JSONRPCResponse.error_response(id=1, error=error)
        assert response.jsonrpc == "2.0"
        assert response.id == 1
        assert response.result is None
        assert response.error.code == ErrorCode.METHOD_NOT_FOUND

    def test_cannot_have_both_result_and_error(self):
        """Test that response cannot have both result and error."""
        with pytest.raises(ValueError):
            JSONRPCResponse(
                id=1,
                result={"data": "test"},
                error=JSONRPCError(code=-32603, message="Error"),
            )

    def test_must_have_result_or_error(self):
        """Test that response must have either result or error."""
        with pytest.raises(ValueError):
            JSONRPCResponse(id=1)


class TestJSONRPCError:
    """Tests for JSONRPCError."""

    def test_parse_error(self):
        """Test creating a parse error."""
        error = JSONRPCError.parse_error("Invalid JSON")
        assert error.code == ErrorCode.PARSE_ERROR
        assert error.message == "Parse error"
        assert error.data == "Invalid JSON"

    def test_invalid_request(self):
        """Test creating an invalid request error."""
        error = JSONRPCError.invalid_request("Missing field")
        assert error.code == ErrorCode.INVALID_REQUEST
        assert error.message == "Invalid request"

    def test_method_not_found(self):
        """Test creating a method not found error."""
        error = JSONRPCError.method_not_found("invalid.method")
        assert error.code == ErrorCode.METHOD_NOT_FOUND
        assert error.message == "Method not found"
        assert error.data == {"method": "invalid.method"}

    def test_invalid_params(self):
        """Test creating an invalid params error."""
        error = JSONRPCError.invalid_params("missing 'path' parameter")
        assert error.code == ErrorCode.INVALID_PARAMS
        assert "missing 'path' parameter" in error.message

    def test_internal_error(self):
        """Test creating an internal error."""
        error = JSONRPCError.internal_error("Database connection failed")
        assert error.code == ErrorCode.INTERNAL_ERROR
        assert "Database connection failed" in error.message

    def test_eval_not_found(self):
        """Test creating an eval not found error."""
        error = JSONRPCError.eval_not_found("/path/to/eval.yaml")
        assert error.code == ErrorCode.EVAL_NOT_FOUND
        assert error.message == "Eval not found"
        assert error.data == {"path": "/path/to/eval.yaml"}

    def test_validation_failed(self):
        """Test creating a validation failed error."""
        errors = ["Missing field: name", "Invalid type: executor"]
        error = JSONRPCError.validation_failed(errors)
        assert error.code == ErrorCode.VALIDATION_FAILED
        assert error.message == "Validation failed"
        assert error.data == {"errors": errors}

    def test_run_failed(self):
        """Test creating a run failed error."""
        error = JSONRPCError.run_failed("Timeout exceeded")
        assert error.code == ErrorCode.RUN_FAILED
        assert "Timeout exceeded" in error.message


class TestJSONRPCNotification:
    """Tests for JSONRPCNotification."""

    def test_valid_notification(self):
        """Test creating a valid notification."""
        notification = JSONRPCNotification(
            method="eval.progress",
            params={
                "runId": "abc123",
                "event": "task_complete",
                "status": "passed",
            },
        )
        assert notification.jsonrpc == "2.0"
        assert notification.method == "eval.progress"
        assert notification.params["runId"] == "abc123"

    def test_notification_without_params(self):
        """Test notification without params."""
        notification = JSONRPCNotification(method="eval.complete")
        assert notification.params is None

    def test_invalid_version(self):
        """Test invalid JSON-RPC version."""
        with pytest.raises(ValidationError):
            JSONRPCNotification(
                jsonrpc="1.0",
                method="test",
            )


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_standard_error_codes(self):
        """Test standard JSON-RPC error codes."""
        assert ErrorCode.PARSE_ERROR == -32700
        assert ErrorCode.INVALID_REQUEST == -32600
        assert ErrorCode.METHOD_NOT_FOUND == -32601
        assert ErrorCode.INVALID_PARAMS == -32602
        assert ErrorCode.INTERNAL_ERROR == -32603

    def test_custom_error_codes(self):
        """Test custom application error codes."""
        assert ErrorCode.EVAL_NOT_FOUND == -32000
        assert ErrorCode.VALIDATION_FAILED == -32001
        assert ErrorCode.RUN_FAILED == -32002
