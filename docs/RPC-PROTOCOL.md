# Waza RPC Protocol Specification

## Design Philosophy

Waza uses a **subprocess-based integration model** rather than a traditional daemon + RPC server. This approach:
- Leverages the existing Python CLI
- Avoids daemon lifecycle management
- Provides natural isolation per evaluation
- Uses standard JSON output that IDEs can easily parse

## Protocol Version: 1.0

### Message Format

Waza emits **line-delimited JSON** on stdout when run with `--stream-json` flag:

```
{"type":"eval_start","eval":"my-eval","tasks":5,"timestamp":1234567890}\n
{"type":"task_start","idx":0,"task":"test-auth","total":5,"timestamp":1234567890}\n
{"type":"task_complete","idx":0,"task":"test-auth","status":"passed","took_ms":1234,"score":1.0,"timestamp":1234567891}\n
{"type":"eval_complete","passed":4,"failed":1,"total":5,"rate":0.8,"timestamp":1234567900}\n
```

### CLI Usage

```bash
# Run with JSON streaming for IDE integration
waza run eval.yaml --stream-json --executor mock

# Optional: Specify model
waza run eval.yaml --stream-json --executor copilot-sdk --model claude-sonnet-4

# Save results to file as well
waza run eval.yaml --stream-json --output results.json
```

**Note:** `--stream-json` automatically disables:
- Rich console output (for clean JSON)
- Interactive prompts (like GitHub issue creation)

### Event Types

#### `eval_start`
Emitted when evaluation begins.
```json
{
  "type": "eval_start",
  "eval": "azure-functions-eval",
  "skill": "azure-functions",
  "tasks": 5,
  "timestamp": 1234567890
}
```

#### `task_start`
Emitted when a task begins execution.
```json
{
  "type": "task_start",
  "idx": 0,
  "name": "test-http-trigger",
  "prompt": "Create an HTTP triggered function..."
}
```

#### `task_progress`
Emitted during task execution (optional, based on executor).
```json
{
  "type": "task_progress",
  "idx": 0,
  "step": "executing",
  "detail": "Calling LLM..."
}
```

#### `task_complete`
Emitted when a task finishes.
```json
{
  "type": "task_complete",
  "idx": 0,
  "task": "test-http-trigger",
  "status": "passed",
  "score": 1.0,
  "took_ms": 2345,
  "timestamp": 1234567891
}
```

**Fields:**
- `status`: "passed" or "failed"
- `score`: 0.0 to 1.0
- `took_ms`: Duration in milliseconds

#### `eval_complete`
Final event with summary.
```json
{
  "type": "eval_complete",
  "passed": 4,
  "failed": 1,
  "total": 5,
  "rate": 0.8,
  "duration_sec": 45.2
}
```

## IDE Integration Patterns

### Pattern 1: Direct Subprocess

**Best for:** VS Code, JetBrains IDEs

IDEs spawn `waza run eval.yaml -v --format json` and parse line-delimited JSON from stdout.

**Advantages:**
- Simple subprocess management
- Real-time progress updates
- No daemon to manage
- Natural per-eval isolation

**Example pseudocode:**
```
process = spawn("waza", ["run", "eval.yaml", "-v", "--format", "json"])
process.stdout.on_line(line => {
  event = JSON.parse(line)
  update_ui(event)
})
```

### Pattern 2: File Watching

**Best for:** Continuous feedback, web dashboards

IDE/tool runs `waza run eval.yaml -o results.json` and watches the output file.

**Advantages:**
- Decoupled from process lifecycle
- Can inspect results offline
- Simple file system API

### Pattern 3: HTTP API (Future)

**Best for:** Web dashboard, remote execution

A separate `waza serve` command starts an HTTP server.

**Endpoints:**
- `POST /api/v1/runs` - Start evaluation
- `GET /api/v1/runs/:id` - Get run status
- `GET /api/v1/runs/:id/stream` - SSE event stream
- `GET /api/v1/evals` - List available evals

## Implementation Priority

1. **✅ Current:** JSON output from Python CLI
2. **🔄 Next:** Line-delimited JSON streaming in `-v` mode
3. **📋 Future:** HTTP API server
4. **📋 Future:** WebSocket support for bidirectional communication

## Security Considerations

- Subprocess approach: IDE controls waza execution, inherits IDE's security context
- HTTP API: Will require authentication tokens
- No credential storage: Waza uses Copilot SDK's auth, delegated to IDE

## Error Handling

Errors are emitted as events:

```json
{
  "type": "error",
  "error_type": "eval_load_failed",
  "message": "Failed to parse eval.yaml: invalid syntax",
  "file": "eval.yaml",
  "line": 15
}
```

Fatal errors also write to stderr and exit with non-zero code.

## Backward Compatibility

The line-delimited JSON format is **additive only**:
- New event types can be added
- New fields can be added to existing events
- Existing fields will never change type or be removed
- IDEs should ignore unknown event types and fields
