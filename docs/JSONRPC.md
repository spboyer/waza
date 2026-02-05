# JSON-RPC Protocol Specification

This document describes the JSON-RPC 2.0 protocol used by waza for IDE integration.

## Overview

waza provides a JSON-RPC 2.0 server that enables IDEs and editors to programmatically run evaluations. The protocol supports:

- Standard JSON-RPC 2.0 request/response pattern
- Real-time progress notifications (server → client)
- Stdio transport (for IDE extensions)
- TCP transport (for remote/debugging)

## Transport

### Stdio (Default)

The server reads JSON-RPC messages from `stdin` and writes responses to `stdout`. Each message is a single line of JSON terminated by a newline character.

```bash
# Start stdio server
waza jsonrpc
```

### TCP (Optional)

For debugging or remote access, the server can listen on a TCP socket:

```bash
# Start TCP server
waza jsonrpc --tcp localhost:9000
```

## Protocol

### Request Format

All requests follow JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "eval.run",
  "params": {
    "path": "/path/to/eval.yaml",
    "executor": "copilot-sdk",
    "model": "claude-sonnet-4-20250514"
  }
}
```

### Response Format

Success response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "runId": "abc123",
    "status": "running"
  }
}
```

Error response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Eval not found",
    "data": {
      "path": "/path/to/eval.yaml"
    }
  }
}
```

### Notification Format

Notifications are sent from server to client without an `id`:

```json
{
  "jsonrpc": "2.0",
  "method": "eval.progress",
  "params": {
    "runId": "abc123",
    "event": "task_complete",
    "taskName": "test-function",
    "status": "passed"
  }
}
```

## Methods

### `eval.run`

Start an eval execution and return a run ID.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "eval.run",
  "params": {
    "path": "/path/to/eval.yaml",          // Required: path to eval.yaml
    "executor": "copilot-sdk",             // Optional: executor type
    "model": "claude-sonnet-4-20250514",   // Optional: model name
    "verbose": true,                       // Optional: verbose output
    "context_dir": "/path/to/context"      // Optional: context directory
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "runId": "abc123",
    "status": "running"
  }
}
```

### `eval.list`

List all available evals in a directory.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "eval.list",
  "params": {
    "directory": "/path/to/evals"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "evals": [
      {
        "path": "/path/to/evals/azure-functions/eval.yaml",
        "name": "azure-functions-eval",
        "skill": "azure-functions",
        "version": "1.0"
      }
    ]
  }
}
```

### `eval.get`

Get details about a specific eval.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "eval.get",
  "params": {
    "path": "/path/to/eval.yaml"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "path": "/path/to/eval.yaml",
    "name": "azure-functions-eval",
    "skill": "azure-functions",
    "version": "1.0",
    "config": {
      "executor": "copilot-sdk",
      "trials_per_task": 3,
      "timeout_seconds": 300
    },
    "metrics": {
      "pass_threshold": 0.8
    }
  }
}
```

### `eval.validate`

Validate an eval spec without running it.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "eval.validate",
  "params": {
    "path": "/path/to/eval.yaml"
  }
}
```

**Response (valid):**

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "valid": true,
    "name": "azure-functions-eval",
    "skill": "azure-functions"
  }
}
```

**Response (invalid):**

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "valid": false,
    "errors": [
      "Missing required field: name",
      "Invalid executor type: invalid"
    ]
  }
}
```

### `task.list`

List all tasks in an eval.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "task.list",
  "params": {
    "path": "/path/to/eval.yaml"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "tasks": [
      {
        "id": "create-function",
        "name": "Create HTTP Function",
        "description": "Create a basic HTTP-triggered function",
        "file": "tasks/create-function.yaml"
      }
    ]
  }
}
```

### `task.get`

Get details about a specific task.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "task.get",
  "params": {
    "path": "/path/to/eval.yaml",
    "taskId": "create-function"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "id": "create-function",
    "name": "Create HTTP Function",
    "description": "Create a basic HTTP-triggered function",
    "prompt": "Create an Azure Function that responds to HTTP requests...",
    "graders": [
      {
        "type": "file_exists",
        "path": "function_app.py"
      }
    ]
  }
}
```

### `run.status`

Get the status of a running eval.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "run.status",
  "params": {
    "runId": "abc123"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "result": {
    "runId": "abc123",
    "status": "running",
    "result": null,
    "error": null
  }
}
```

### `run.cancel`

Cancel a running eval.

**Request:**

```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "method": "run.cancel",
  "params": {
    "runId": "abc123"
  }
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "result": {
    "runId": "abc123",
    "status": "cancelled"
  }
}
```

## Notifications

Notifications are sent from the server to the client during eval execution. They do not have an `id` field and do not expect a response.

### `eval.progress`

Sent during eval execution to report progress.

```json
{
  "jsonrpc": "2.0",
  "method": "eval.progress",
  "params": {
    "runId": "abc123",
    "event": "task_complete",
    "taskName": "create-function",
    "taskNum": 1,
    "totalTasks": 5,
    "status": "passed"
  }
}
```

**Event types:**
- `run_start` - Eval run started
- `task_start` - Task execution started
- `trial_start` - Trial execution started
- `trial_complete` - Trial completed
- `task_complete` - Task completed (all trials finished)
- `run_complete` - Eval run completed

### `eval.log`

Sent to stream real-time log output.

```json
{
  "jsonrpc": "2.0",
  "method": "eval.log",
  "params": {
    "runId": "abc123",
    "level": "info",
    "message": "Running task: create-function"
  }
}
```

### `eval.complete`

Sent when an eval run completes (success or failure).

**Success:**

```json
{
  "jsonrpc": "2.0",
  "method": "eval.complete",
  "params": {
    "runId": "abc123",
    "summary": {
      "total": 5,
      "passed": 4,
      "failed": 1,
      "passRate": 0.8
    }
  }
}
```

**Failure:**

```json
{
  "jsonrpc": "2.0",
  "method": "eval.complete",
  "params": {
    "runId": "abc123",
    "error": "Eval execution failed: timeout exceeded"
  }
}
```

## Error Codes

| Code | Message | Meaning |
|------|---------|---------|
| -32700 | Parse error | Invalid JSON received |
| -32600 | Invalid request | Not a valid JSON-RPC request |
| -32601 | Method not found | Unknown method name |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Server internal error |
| -32000 | Eval not found | Eval file does not exist |
| -32001 | Validation failed | Eval spec is invalid |
| -32002 | Run failed | Eval execution failed |

## Example Client

Here's a simple Python client example:

```python
import json
import sys
import subprocess

class WazaClient:
    def __init__(self):
        # Start waza jsonrpc server
        self.proc = subprocess.Popen(
            ["waza", "jsonrpc"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.request_id = 0
    
    def send_request(self, method, params):
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        # Send request
        self.proc.stdin.write(json.dumps(request) + "\n")
        self.proc.stdin.flush()
        
        # Read response
        response_line = self.proc.stdout.readline()
        return json.loads(response_line)
    
    def read_notification(self):
        """Read a notification (non-blocking)."""
        line = self.proc.stdout.readline()
        if line:
            return json.loads(line)
        return None
    
    def close(self):
        self.proc.stdin.close()
        self.proc.wait()

# Usage
client = WazaClient()

# Run an eval
response = client.send_request("eval.run", {
    "path": "/path/to/eval.yaml",
    "executor": "copilot-sdk"
})
print(f"Started run: {response['result']['runId']}")

# Read progress notifications
while True:
    notification = client.read_notification()
    if notification and notification.get("method") == "eval.complete":
        print(f"Run complete: {notification['params']}")
        break

client.close()
```

## IDE Integration

The JSON-RPC server is designed for IDE extensions:

### VS Code Extension

```typescript
import { spawn } from 'child_process';

const waza = spawn('waza', ['jsonrpc']);

// Send request
const request = {
  jsonrpc: '2.0',
  id: 1,
  method: 'eval.run',
  params: { path: '/path/to/eval.yaml' }
};
waza.stdin.write(JSON.stringify(request) + '\n');

// Read responses
waza.stdout.on('data', (data) => {
  const message = JSON.parse(data.toString());
  if (message.method === 'eval.progress') {
    // Update progress bar
  }
});
```

### JetBrains Plugin

```kotlin
val process = ProcessBuilder("waza", "jsonrpc").start()
val writer = BufferedWriter(OutputStreamWriter(process.outputStream))
val reader = BufferedReader(InputStreamReader(process.inputStream))

// Send request
val request = JSONObject()
    .put("jsonrpc", "2.0")
    .put("id", 1)
    .put("method", "eval.run")
    .put("params", JSONObject().put("path", "/path/to/eval.yaml"))

writer.write(request.toString())
writer.newLine()
writer.flush()

// Read response
val response = JSONObject(reader.readLine())
```

## Testing

You can test the JSON-RPC server using standard input:

```bash
# Start server
waza jsonrpc

# Send request (type or paste)
{"jsonrpc":"2.0","id":1,"method":"eval.list","params":{"directory":"./examples"}}

# Press Enter to send
```

Or use a simple script:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"eval.list","params":{"directory":"./examples"}}' | waza jsonrpc
```

For TCP testing:

```bash
# Terminal 1: Start TCP server
waza jsonrpc --tcp localhost:9000

# Terminal 2: Send request with nc
echo '{"jsonrpc":"2.0","id":1,"method":"eval.list","params":{"directory":"./examples"}}' | nc localhost 9000
```
