# Waza IDE Extensions

This directory contains IDE integration documentation and starter templates.

## Integration Philosophy

Waza uses a **CLI-first approach** rather than traditional RPC servers:

- IDEs spawn `waza` as subprocess
- Parse line-delimited JSON from stdout  
- No daemon, no sockets, no complex lifecycle
- Each eval runs in isolated process

## Supported IDEs

### VS Code

See `vscode-integration.md` for subprocess-based integration pattern.

**Key Features:**
- Run evaluations from command palette
- Real-time progress in status bar
- Results viewer with charts
- Task list in sidebar

### JetBrains IDEs

See `jetbrains-integration.md` for IntelliJ Platform integration.

**Key Features:**
- Tool window with eval list
- Run configurations for evals
- Inline results in editor
- Test runner integration

## Quick Start

### For IDE Extension Developers

1. **Spawn waza subprocess:**
   ```
   waza run eval.yaml -v --format json
   ```

2. **Parse stdout (line-delimited JSON):**
   ```json
   {"type":"task_start","idx":0,"name":"test-auth"}
   {"type":"task_complete","idx":0,"result":"pass"}
   ```

3. **Update your UI based on events**

4. **Handle completion/errors via exit code**

That's it! No RPC protocol to implement, no server to manage.

## Protocol Documentation

See `/docs/RPC-PROTOCOL.md` for complete message format specification.

## Extension Status

- [x] Protocol specification
- [x] Integration documentation
- [ ] VS Code extension (community contribution welcome)
- [ ] JetBrains plugin (community contribution welcome)
- [ ] Emacs mode (community contribution welcome)
- [ ] Vim plugin (community contribution welcome)

## Contributing

We welcome community contributions for IDE extensions! The protocol is stable and documented. See `/docs/RPC-PROTOCOL.md` for details.

**Guidelines:**
- Use subprocess execution, not RPC/sockets
- Parse line-delimited JSON from stdout
- Handle all event types gracefully
- Ignore unknown events (forward compatibility)
- Test with mock executor first

## Examples

### Minimal Python Integration

```python
import subprocess
import json

proc = subprocess.Popen(
    ["waza", "run", "eval.yaml", "-v", "--format", "json"],
    stdout=subprocess.PIPE,
    text=True
)

for line in proc.stdout:
    event = json.loads(line)
    print(f"Event: {event['type']}")
    if event['type'] == 'task_complete':
        print(f"  Task {event['name']}: {event['result']}")
```

### Minimal JavaScript Integration

```javascript
const { spawn } = require('child_process');

const proc = spawn('waza', ['run', 'eval.yaml', '-v', '--format', 'json']);

proc.stdout.on('data', (data) => {
  const lines = data.toString().split('\n');
  for (const line of lines) {
    if (!line.trim()) continue;
    const event = JSON.parse(line);
    console.log(`Event: ${event.type}`);
  }
});
```

## Future: HTTP API

For web dashboards and remote execution, we're planning `waza serve`:

```bash
waza serve --port 8080
```

This will expose:
- REST API for eval management
- SSE streaming for real-time progress
- Static web dashboard

See `/docs/WEB-DASHBOARD.md` for architecture.
