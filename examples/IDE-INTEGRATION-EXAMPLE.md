# Waza IDE Integration Example

This example demonstrates how to integrate waza into an IDE or tool using its JSON streaming protocol.

## Overview

The `ide_integration_example.py` script shows the complete integration pattern:

1. **Spawn waza subprocess** with `--stream-json` flag
2. **Parse line-delimited JSON** events from stdout
3. **Update UI in real-time** based on events
4. **Handle completion** and display summary

## Running the Example

```bash
# Run with mock executor (fast, no LLM calls)
python examples/ide_integration_example.py examples/code-explainer/eval.yaml

# The script will display:
# - Real-time progress as tasks execute
# - Pass/fail indicators with timing
# - Final summary with statistics
```

## Output

```
Starting evaluation: examples/code-explainer/eval.yaml
------------------------------------------------------------
[19:22:41] Starting eval: code-explainer-eval
            Skill: code-explainer
            Tasks: 4

[19:22:41] [1/4] Task started: Explain SQL JOIN Query
[19:22:41]       ✓ passed (100ms, score: 1.00)
[19:22:41] [2/4] Task started: Explain List Comprehension
[19:22:41]       ✓ passed (100ms, score: 1.00)
...

============================================================
Evaluation completed successfully!

Results:
  Passed: 4/4
  Failed: 0/4
  Pass Rate: 100.0%
```

## Key Integration Points

### 1. Spawning Waza

```python
proc = subprocess.Popen(
    ["waza", "run", eval_path, "--stream-json", "--executor", "mock"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1  # Line buffered
)
```

### 2. Parsing Events

```python
for line in proc.stdout:
    if line.strip():
        event = json.loads(line)
        handle_event(event)
```

### 3. Handling Event Types

```python
def handle_event(event):
    event_type = event.get("type")
    
    if event_type == "eval_start":
        # Initialize UI, show eval info
        pass
        
    elif event_type == "task_start":
        # Update progress, show current task
        pass
        
    elif event_type == "task_complete":
        # Update task status, show results
        status = event.get("status")  # "passed" or "failed"
        took_ms = event.get("took_ms")
        score = event.get("score")
        
    elif event_type == "eval_complete":
        # Show final summary
        passed = event.get("passed")
        failed = event.get("failed")
        pass_rate = event.get("rate")
```

## Integration Best Practices

### Error Handling

- Check subprocess exit code
- Parse stderr for error messages
- Handle malformed JSON gracefully
- Timeout protection for long-running evals

### UI Updates

- Use event timestamps for accurate timing
- Buffer events if UI can't keep up
- Show progress percentage: `(idx / total) * 100`
- Color-code status: green for passed, red for failed

### User Experience

- Allow cancellation (send SIGTERM to process)
- Show real-time feedback (don't wait for completion)
- Display task details on click/hover
- Link to full results file if `--output` used

## Adapting for Your IDE

### VS Code Extension

```typescript
const proc = spawn('waza', ['run', evalPath, '--stream-json']);

proc.stdout.on('data', (data: Buffer) => {
  const lines = data.toString().split('\n');
  for (const line of lines) {
    if (line.trim()) {
      const event = JSON.parse(line);
      updateProgress(event);
    }
  }
});
```

### JetBrains Plugin

```kotlin
val proc = ProcessBuilder("waza", "run", evalPath, "--stream-json").start()

BufferedReader(InputStreamReader(proc.inputStream)).use { reader ->
    var line: String?
    while (reader.readLine().also { line = it } != null) {
        val event = JSONObject(line)
        handleEvent(event)
    }
}
```

### Emacs

```elisp
(defun waza-run-eval (eval-path)
  (let ((proc (start-process "waza" "*waza*" "waza" "run" eval-path "--stream-json")))
    (set-process-filter proc 'waza-process-filter)))

(defun waza-process-filter (proc string)
  (dolist (line (split-string string "\n" t))
    (let ((event (json-parse-string line)))
      (waza-handle-event event))))
```

## See Also

- [RPC Protocol Documentation](../docs/RPC-PROTOCOL.md) - Complete event reference
- [IDE Integration Guide](../docs/IDE-INTEGRATION.md) - Architecture overview
- [Web Dashboard Design](../docs/WEB-DASHBOARD.md) - HTTP API approach

## Questions?

Check the [documentation](../docs/) or open an issue on GitHub.
