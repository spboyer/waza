# Waza IDE Integration Architecture

## Overview

This document describes how IDEs (VS Code, JetBrains, etc.) can integrate with waza for Agent Skills evaluation.

## Integration Approach

Rather than implementing a traditional JSON-RPC server, waza uses a **subprocess-based integration** where IDEs launch waza CLI commands and parse structured output.

### Why Subprocess Instead of RPC?

1. **Simpler integration** - IDEs already have excellent subprocess support
2. **No daemon management** - Each eval is isolated
3. **Standard JSON output** - Easy to parse, already implemented in Python version
4. **Natural progress streaming** - Use standard output with line-delimited JSON

## IDE Integration Methods

### Method 1: Direct CLI Execution (Recommended)

IDEs execute waza CLI commands and parse JSON output:

```bash
# Run eval with JSON streaming
waza run eval.yaml --stream-json

# With specific executor/model
waza run eval.yaml --stream-json --executor mock

# Save results to file as well
waza run eval.yaml --stream-json --output results.json
```

**Output Format:**
```jsonlines
{"type":"eval_start","eval":"my-eval","tasks":5,"timestamp":1234567890}
{"type":"task_start","idx":0,"task":"test-auth","total":5,"timestamp":1234567890}
{"type":"task_complete","idx":0,"task":"test-auth","status":"passed","took_ms":1234,"score":1.0,"timestamp":1234567891}
{"type":"eval_complete","passed":4,"failed":1,"total":5,"rate":0.8,"timestamp":1234567900}
```

### Method 2: Watch Mode with File System

For continuous feedback:

```bash
# Run in watch mode - rewrites results.json on changes
waza watch eval.yaml --output results.json
```

IDEs can watch `results.json` for changes using their file system watchers.

### Method 3: HTTP API (Future)

For web dashboard and remote execution:

```bash
# Start HTTP server
waza serve --port 8080

# API endpoints:
# GET  /api/evals          - List available evals
# POST /api/evals/:id/run  - Execute eval
# GET  /api/runs/:id       - Get run status
# GET  /api/runs/:id/stream - SSE event stream
```

## VS Code Extension Architecture

```
waza-vscode/
├── src/
│   ├── extension.ts        # Extension entry point
│   ├── wazaRunner.ts       # Subprocess executor
│   ├── resultsParser.ts    # Parse JSON output
│   └── views/
│       ├── resultsView.ts  # Show eval results
│       └── tasksView.ts    # Tree view of tasks
└── package.json
```

**Key Components:**

1. **WazaRunner** - Spawns waza CLI, captures stdout
2. **ResultsParser** - Parses line-delimited JSON progress
3. **ResultsView** - Webview showing eval results with charts
4. **TasksView** - Tree view in sidebar showing task status

## JetBrains Plugin Architecture

```
waza-intellij/
├── src/main/kotlin/
│   ├── WazaToolWindow.kt       # Tool window UI
│   ├── WazaProcessRunner.kt    # Execute waza CLI
│   └── WazaResultsParser.kt    # Parse output
└── resources/
    └── META-INF/plugin.xml
```

## Protocol Specification

### Progress Events (stdout, line-delimited JSON)

```typescript
// Event types emitted during eval execution
type ProgressEvent = 
  | { type: "eval_start", name: string, tasks: number }
  | { type: "task_start", task: string, num: number, total: number }
  | { type: "task_progress", task: string, message: string }
  | { type: "task_complete", task: string, status: "passed"|"failed", duration_ms: number }
  | { type: "eval_complete", summary: { total: number, passed: number, failed: number } }
```

### Results File Format (JSON)

```json
{
  "eval_name": "azure-functions-eval",
  "skill": "azure-functions",
  "run_id": "run-1234567890",
  "started_at": "2026-02-05T19:00:00Z",
  "completed_at": "2026-02-05T19:05:30Z",
  "summary": {
    "total_tasks": 5,
    "passed": 4,
    "failed": 1,
    "pass_rate": 0.8
  },
  "tasks": [
    {
      "id": "test-auth",
      "name": "Test authentication flow",
      "status": "passed",
      "duration_ms": 1234,
      "trials": [...]
    }
  ]
}
```

## Implementation Status

- [x] Python CLI with JSON output (current implementation)
- [ ] Line-delimited JSON progress streaming in verbose mode
- [ ] `waza watch` command for continuous eval
- [ ] VS Code extension skeleton
- [ ] JetBrains plugin skeleton
- [ ] HTTP API server (`waza serve`)
- [ ] Web dashboard frontend

## Next Steps

1. **Enhance Python CLI** - Add line-delimited JSON progress to verbose mode
2. **Create extension skeletons** - Basic VS Code/JetBrains integration
3. **Optional: HTTP API** - For web dashboard and remote access

## Benefits of This Approach

- **Leverage existing Python implementation** - No need to port to Go immediately
- **Standard IDE integration patterns** - Subprocess execution is well-supported
- **Simple deployment** - Just install waza CLI, no daemon
- **Easy debugging** - Can run commands manually
- **Natural isolation** - Each eval runs in separate process
