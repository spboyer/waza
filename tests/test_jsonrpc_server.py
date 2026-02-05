"""Tests for JSON-RPC server implementation."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from waza.jsonrpc.protocol import JSONRPCError
from waza.jsonrpc.server import JSONRPCServer
from waza.jsonrpc.transports import Transport


class MockTransport(Transport):
    """Mock transport for testing."""

    def __init__(self):
        """Initialize mock transport."""
        self.messages_to_read = []
        self.written_messages = []
        self.closed = False

    async def read_message(self):
        """Read next message from queue."""
        if not self.messages_to_read:
            return None
        return self.messages_to_read.pop(0)

    async def write_message(self, message):
        """Write message to output queue."""
        self.written_messages.append(message)

    async def close(self):
        """Close transport."""
        self.closed = True

    def add_message(self, message):
        """Add message to read queue."""
        self.messages_to_read.append(message)


class TestJSONRPCServer:
    """Tests for JSONRPCServer."""

    @pytest.mark.asyncio
    async def test_handle_valid_request(self):
        """Test handling a valid request."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        # Add a request
        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eval.validate",
            "params": {"path": "/nonexistent/eval.yaml"},
        })
        transport.add_message(None)  # Signal end

        # Run server
        await server.serve()

        # Check response
        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        # Should have error since file doesn't exist
        assert "error" in response

    @pytest.mark.asyncio
    async def test_handle_invalid_request(self):
        """Test handling an invalid request."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        # Add invalid request (missing method)
        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "params": {},
        })
        transport.add_message(None)

        # Run server
        await server.serve()

        # Check error response
        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == -32600  # Invalid request

    @pytest.mark.asyncio
    async def test_handle_method_not_found(self):
        """Test handling unknown method."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        # Add request with unknown method
        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "unknown.method",
            "params": {},
        })
        transport.add_message(None)

        # Run server
        await server.serve()

        # Check error response
        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert response["jsonrpc"] == "2.0"
        assert response["error"]["code"] == -32601  # Method not found

    @pytest.mark.asyncio
    async def test_handle_notification(self):
        """Test handling a notification (no response expected)."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        # Add notification (no id)
        transport.add_message({
            "jsonrpc": "2.0",
            "method": "eval.cancel",
            "params": {"runId": "abc"},
        })
        transport.add_message(None)

        # Run server
        await server.serve()

        # Should not write any response for notification
        assert len(transport.written_messages) == 0

    @pytest.mark.asyncio
    async def test_handle_parse_error(self):
        """Test handling JSON parse error."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        # Mock read_message to raise JSONDecodeError
        original_read = transport.read_message
        
        async def read_with_error():
            if transport.messages_to_read:
                raise json.JSONDecodeError("Invalid JSON", "", 0)
            return None
        
        transport.read_message = read_with_error
        transport.add_message({})  # Trigger error

        # Run server
        await server.serve()

        # Should write parse error response
        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert response["error"]["code"] == -32700  # Parse error

    @pytest.mark.asyncio
    async def test_server_stop(self):
        """Test stopping the server."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        # Stop server
        await server.stop()

        # Transport should be closed
        assert transport.closed


class TestMethodHandlers:
    """Tests for method handlers."""

    @pytest.fixture
    def temp_eval(self, tmp_path):
        """Create a temporary eval file for testing."""
        eval_yaml = tmp_path / "eval.yaml"
        eval_yaml.write_text("""
name: test-eval
skill: test-skill
version: "1.0"

config:
  executor: mock
  trials_per_task: 1

tasks:
  - file: tasks/task1.yaml
""")
        
        # Create tasks directory and task file
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir()
        task_file = tasks_dir / "task1.yaml"
        task_file.write_text("""
id: task-1
name: Test Task
description: A test task
prompt: Do something
""")
        
        return eval_yaml

    @pytest.mark.asyncio
    async def test_eval_validate_valid(self, temp_eval):
        """Test validating a valid eval."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eval.validate",
            "params": {"path": str(temp_eval)},
        })
        transport.add_message(None)

        await server.serve()

        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert response["result"]["valid"] is True
        assert response["result"]["name"] == "test-eval"

    @pytest.mark.asyncio
    async def test_eval_validate_not_found(self):
        """Test validating a non-existent eval."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eval.validate",
            "params": {"path": "/nonexistent/eval.yaml"},
        })
        transport.add_message(None)

        await server.serve()

        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert "error" in response
        assert response["error"]["code"] == -32000  # Eval not found

    @pytest.mark.asyncio
    async def test_eval_get(self, temp_eval):
        """Test getting eval details."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eval.get",
            "params": {"path": str(temp_eval)},
        })
        transport.add_message(None)

        await server.serve()

        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert "result" in response
        assert response["result"]["name"] == "test-eval"
        assert response["result"]["skill"] == "test-skill"
        assert response["result"]["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_task_list(self, temp_eval):
        """Test listing tasks."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "task.list",
            "params": {"path": str(temp_eval)},
        })
        transport.add_message(None)

        await server.serve()

        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert "result" in response
        assert "tasks" in response["result"]
        assert len(response["result"]["tasks"]) == 1
        assert response["result"]["tasks"][0]["id"] == "task-1"

    @pytest.mark.asyncio
    async def test_task_get(self, temp_eval):
        """Test getting task details."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "task.get",
            "params": {"path": str(temp_eval), "taskId": "task-1"},
        })
        transport.add_message(None)

        await server.serve()

        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert "result" in response
        assert response["result"]["id"] == "task-1"
        assert response["result"]["name"] == "Test Task"

    @pytest.mark.asyncio
    async def test_eval_list(self, tmp_path):
        """Test listing evals in a directory."""
        # Create multiple eval files
        eval1 = tmp_path / "eval1.yaml"
        eval1.write_text("""
name: eval-1
skill: skill-1
version: "1.0"
config:
  executor: mock
tasks: []
""")
        
        eval2 = tmp_path / "eval2.yaml"
        eval2.write_text("""
name: eval-2
skill: skill-2
version: "1.0"
config:
  executor: mock
tasks: []
""")

        transport = MockTransport()
        server = JSONRPCServer(transport)

        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eval.list",
            "params": {"directory": str(tmp_path)},
        })
        transport.add_message(None)

        await server.serve()

        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert "result" in response
        assert len(response["result"]["evals"]) == 2

    @pytest.mark.asyncio
    async def test_invalid_params(self):
        """Test method with invalid parameters."""
        transport = MockTransport()
        server = JSONRPCServer(transport)

        # Missing required 'path' parameter
        transport.add_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eval.validate",
            "params": {},
        })
        transport.add_message(None)

        await server.serve()

        assert len(transport.written_messages) == 1
        response = transport.written_messages[0]
        assert "error" in response
        assert response["error"]["code"] == -32602  # Invalid params
