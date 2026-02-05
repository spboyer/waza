# Waza Web Dashboard Architecture

## Overview

The web dashboard provides a visual interface for managing and monitoring Agent Skills evaluations. Unlike traditional web apps, Waza's dashboard operates in two modes:

1. **Local Mode**: Direct filesystem access, launches waza CLI subprocesses
2. **Server Mode**: HTTP API backend with remote execution

## Architecture Decision

We are implementing **Server Mode first** because:
- It's more useful for team collaboration
- Can be deployed to shared environments
- Local mode can shell out to `waza serve --local`

## Technology Stack

### Backend: Python (FastAPI)
- Leverage existing waza Python codebase
- FastAPI for async HTTP + SSE streaming
- Uvicorn ASGI server
- SQLite for run history

### Frontend: Static HTML + Vanilla JS
- No build step required
- Can be served by FastAPI's static files
- Lightweight, fast to load
- Progressive enhancement

**Why not React/Vue?**
- Adds build complexity
- Waza is a CLI tool first
- Want minimal dependencies
- Can upgrade later if needed

## API Design

### REST Endpoints

```
GET  /api/evals              List evals in ~/.waza/
POST /api/evals              Create new eval
GET  /api/evals/:id          Get eval details
PUT  /api/evals/:id          Update eval
DELETE /api/evals/:id        Delete eval

GET  /api/evals/:id/tasks    List tasks in eval
POST /api/evals/:id/tasks    Add task to eval

POST /api/runs               Start eval execution
GET  /api/runs/:id           Get run status
GET  /api/runs               List recent runs
GET  /api/runs/:id/stream    SSE event stream
```

### SSE Streaming Format

Real-time progress via Server-Sent Events:

```
event: task_start
data: {"idx":0,"name":"test-auth"}

event: task_complete  
data: {"idx":0,"result":"pass","took_ms":1234}

event: eval_complete
data: {"passed":4,"failed":1}
```

## File Structure

```
waza/
├── api/
│   ├── __init__.py
│   ├── server.py          # FastAPI app
│   ├── routes/
│   │   ├── evals.py       # Eval management
│   │   ├── runs.py        # Run execution
│   │   └── stream.py      # SSE streaming
│   ├── storage.py         # Filesystem + SQLite
│   └── models.py          # Pydantic models
└── web/
    ├── index.html         # Dashboard home
    ├── eval.html          # Eval detail view
    ├── run.html           # Run detail view
    ├── app.js             # Main JS
    └── style.css          # Styling
```

## Data Storage

### Evals Storage
- Location: `~/.waza/evals/`
- Format: One directory per eval
- Structure:
  ```
  ~/.waza/evals/
  └── my-eval/
      ├── eval.yaml
      ├── tasks/
      │   ├── task1.yaml
      │   └── task2.yaml
      └── fixtures/
          └── example.txt
  ```

### Runs Storage
- Location: `~/.waza/runs/`
- Format: SQLite database + JSON artifacts
- Schema:
  ```sql
  CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    eval_id TEXT,
    started_at INTEGER,
    completed_at INTEGER,
    status TEXT,
    summary JSON
  );
  
  CREATE TABLE task_results (
    run_id TEXT,
    task_idx INTEGER,
    task_name TEXT,
    status TEXT,
    score REAL,
    duration_ms INTEGER,
    PRIMARY KEY (run_id, task_idx)
  );
  ```

## UI Components

### Dashboard View
- List of evals with quick stats
- Recent runs timeline
- Quick run button per eval

### Eval Detail View
- Task list (editable)
- Configuration panel
- Historical results chart
- Run eval button

### Run Detail View
- Progress bar
- Task results table
- Expandable transcript per task
- Suggestions for failed tasks
- Export button (JSON, Markdown)

## Implementation Plan

### Phase 1: Basic Server
- [ ] FastAPI app setup
- [ ] Static file serving
- [ ] Storage layer (filesystem + SQLite)
- [ ] Basic eval list/detail endpoints
- [ ] Simple HTML dashboard

### Phase 2: Eval Execution
- [ ] Run creation endpoint
- [ ] Background task execution
- [ ] SSE streaming integration
- [ ] Run history persistence

### Phase 3: Interactive Features
- [ ] Task editing
- [ ] Eval creation wizard
- [ ] Real-time dashboard updates
- [ ] Run comparison view

### Phase 4: Polish
- [ ] Authentication (optional)
- [ ] Multi-user support
- [ ] Export/import evals
- [ ] Dark mode

## Security

- **Local-only by default**: Binds to 127.0.0.1
- **Optional auth**: `--require-auth` flag generates API token
- **No eval execution without confirmation** for remote mode
- **Filesystem sandboxing**: Only accesses ~/.waza/ directory

## CLI Integration

```bash
# Start server
waza serve

# With custom port
waza serve --port 3000

# With authentication
waza serve --require-auth

# Local mode (no network, direct filesystem)
waza serve --local --no-execute
```

## Future Enhancements

- WebSocket for bidirectional communication
- Collaborative eval editing
- GitHub integration for eval synchronization
- Skill discovery from GitHub repos
- Model performance comparison dashboard
