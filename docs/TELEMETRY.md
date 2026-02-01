# Runtime Telemetry

Capture and analyze metrics from skills running in production.

## Overview

Runtime telemetry enables you to:
1. **Capture** - Collect events during live skill execution
2. **Analyze** - Compute metrics from captured sessions
3. **Convert** - Transform telemetry into eval tasks for regression testing

## Quick Start

### Collecting Telemetry

```python
from waza.telemetry import RuntimeCollector

# Create collector
collector = RuntimeCollector()

# Start a session when user invokes skill
session_id = collector.start_session(
    prompt="Deploy my app to Azure",
    metadata={"user_id": "user123", "environment": "production"}
)

# Record events as they happen
collector.record_event(session_id, "skill.invoked", skill_name="azure-deploy")
collector.record_event(session_id, "tool.called", data={"tool": "az", "args": ["webapp", "create"]})
collector.record_event(session_id, "tool.completed", data={"tool": "az", "success": True})

# End session
collector.end_session(
    session_id,
    output="Deployed to https://myapp.azurewebsites.net",
    success=True
)

# Export for analysis
collector.export_to_file("telemetry/sessions-2024-01.json")
```

### Analyzing Telemetry

```bash
# Analyze telemetry file
waza analyze telemetry/sessions-2024-01.json

# Filter to specific skill
waza analyze telemetry/ --skill azure-deploy

# Export analysis
waza analyze telemetry/ -o analysis-report.json
```

### Output

```
Runtime Telemetry Analysis

Sessions analyzed: 1,234
Skills invoked: azure-deploy, azure-create-app, azure-diagnostics

                Runtime Metrics                
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Metric                    ┃ Value          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ success_rate              │         94.2%  │
│ avg_duration_ms           │         2,340  │
│ total_tool_calls          │         8,921  │
│ avg_tool_calls_per_session│           7.2  │
└───────────────────────────┴────────────────┘
```

## Telemetry Schema

### Session

```python
@dataclass
class SessionTelemetry:
    session_id: str
    start_time: datetime
    end_time: datetime | None
    skill_name: str | None
    prompt: str
    output: str
    events: list[TelemetryEvent]
    tool_calls: list[dict]
    success: bool
    error: str | None
    metadata: dict
```

### Event

```python
@dataclass
class TelemetryEvent:
    timestamp: datetime
    event_type: str
    skill_name: str | None
    data: dict
    session_id: str | None
```

### Event Types

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `skill.invoked` | Skill was triggered | `skill_name` |
| `tool.called` | Tool execution started | `tool`, `args` |
| `tool.completed` | Tool execution finished | `tool`, `success`, `error` |
| `llm.request` | LLM API call made | `model`, `tokens` |
| `llm.response` | LLM response received | `model`, `latency_ms` |
| `error` | Error occurred | `error_type`, `message` |

## Integration Patterns

### 1. Middleware/Hook Integration

For skills running in a runtime with hooks:

```python
# In your skill runtime
from waza.telemetry import RuntimeCollector

collector = RuntimeCollector()

def on_skill_start(prompt, context):
    return collector.start_session(prompt, metadata=context)

def on_skill_event(session_id, event_type, data):
    collector.record_event(session_id, event_type, data=data)

def on_skill_complete(session_id, output, success, error=None):
    collector.end_session(session_id, output, success, error)
    
# Periodically export
collector.export_to_file(f"telemetry/{date.today()}.json")
```

### 2. Log Parsing

If you have existing logs, parse them into telemetry format:

```python
from waza.telemetry import SessionTelemetry, TelemetryEvent
from datetime import datetime
import json

def parse_log_line(line):
    data = json.loads(line)
    return TelemetryEvent(
        timestamp=datetime.fromisoformat(data["timestamp"]),
        event_type=data["event"],
        skill_name=data.get("skill"),
        data=data.get("data", {}),
    )

# Group events by session and create SessionTelemetry objects
```

### 3. Webhook Integration

Receive telemetry from remote sources:

```python
from flask import Flask, request
from waza.telemetry import RuntimeCollector

app = Flask(__name__)
collector = RuntimeCollector()

@app.route("/telemetry/session/start", methods=["POST"])
def start_session():
    data = request.json
    session_id = collector.start_session(data["prompt"], data.get("metadata"))
    return {"session_id": session_id}

@app.route("/telemetry/session/<session_id>/event", methods=["POST"])
def record_event(session_id):
    data = request.json
    collector.record_event(session_id, data["event_type"], data.get("data"))
    return {"ok": True}
```

## Converting to Eval Tasks

Transform runtime sessions into eval tasks for regression testing:

```python
from waza.telemetry import TelemetryAnalyzer, RuntimeCollector

analyzer = TelemetryAnalyzer()
sessions = RuntimeCollector.load_from_file("telemetry/sessions.json")

# Convert interesting sessions to eval tasks
for session in sessions:
    if session.success and session.skill_name == "azure-deploy":
        task = analyzer.to_eval_input(session)
        
        # task is now:
        # {
        #     "id": "runtime-abc123",
        #     "name": "Runtime session abc123",
        #     "inputs": {"prompt": "...", "context": {...}},
        #     "captured": {"output": "...", "tool_calls": [...]}
        # }
        
        # Add expected outcomes based on captured behavior
        task["expected"] = {
            "output_contains": ["azurewebsites.net"],
            "outcomes": [{"type": "task_completed"}]
        }
        
        # Save as eval task
        with open(f"tasks/{task['id']}.yaml", "w") as f:
            yaml.dump(task, f)
```

## Metrics Reference

### Aggregate Metrics

| Metric | Description |
|--------|-------------|
| `success_rate` | Percentage of sessions that succeeded |
| `avg_duration_ms` | Average session duration |
| `total_tool_calls` | Total tool invocations across all sessions |
| `avg_tool_calls_per_session` | Average tools used per session |

### Per-Skill Metrics

| Metric | Description |
|--------|-------------|
| `invocations` | Number of times skill was invoked |
| `success_rate` | Skill-specific success rate |
| `avg_duration_ms` | Average duration for this skill |
| `total_tool_calls` | Tools used by this skill |

## Best Practices

1. **Sample in production** - Don't capture 100% of sessions; sample 1-10%
2. **Anonymize data** - Remove PII before exporting telemetry
3. **Set retention** - Delete old telemetry after analysis
4. **Monitor costs** - Track storage costs for telemetry data
5. **Alert on anomalies** - Set up alerts for sudden drops in success_rate
