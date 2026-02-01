# Web UI Documentation

## Overview

The skill-eval Web UI provides a modern dashboard for creating, editing, and running eval suites visually with real-time updates.

## Quick Start

### Starting the Web UI

```bash
# Install web dependencies (first time only)
pip install skill-eval[web]

# Or install manually
pip install fastapi uvicorn[standard]

# Start the server
skill-eval serve

# Custom port
skill-eval serve --port 3000

# Development mode with auto-reload
skill-eval serve --reload
```

The server will start on `http://localhost:8000` by default:
- **Web UI**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/api/health

## Features

### Dashboard

The main dashboard provides an overview of your eval suites:

- **Total Evals**: Count of all eval suites
- **Model**: Currently configured model
- **Executor**: Currently configured executor (mock or copilot-sdk)
- **Eval Suites List**: All available eval suites with quick actions

### API Endpoints

The FastAPI backend provides a RESTful API for all operations:

#### Evals
- `GET /api/evals` - List all eval suites
- `GET /api/evals/{id}` - Get a specific eval suite
- `POST /api/evals` - Create a new eval suite
- `PUT /api/evals/{id}` - Update an eval suite
- `DELETE /api/evals/{id}` - Delete an eval suite

#### Runs
- `GET /api/runs` - List all runs
- `GET /api/runs/{id}` - Get run results
- `POST /api/runs` - Start a new run
- `GET /api/runs/{id}/stream` - Stream real-time updates (SSE)

#### Config
- `GET /api/config` - Get user configuration
- `PUT /api/config` - Update configuration

#### Skills (Coming Soon)
- `POST /api/skills/scan` - Scan GitHub repo for skills (requires auth)
- `POST /api/skills/generate` - Generate eval from SKILL.md (requires auth)

## Data Storage

All data is stored in `~/.skill-eval/` as JSON and YAML files:

```
~/.skill-eval/
├── config.json              # User preferences
├── evals/                   # Eval suite definitions
│   ├── my-skill-eval.yaml
│   └── another-eval.yaml
├── runs/                    # Run history
│   ├── 2026-02-01-123456-my-skill/
│   │   ├── results.json
│   │   ├── transcript.json
│   │   └── suggestions.md
│   └── ...
└── cache/                   # Temp files
```

## Development

### Frontend Development

The frontend is a React + TypeScript app built with Vite:

```bash
# Navigate to web directory
cd web/

# Install dependencies
npm install

# Start dev server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The frontend dev server runs on `http://localhost:5173` and proxies API requests to the backend.

### Backend Development

The backend is a FastAPI app:

```bash
# Start with auto-reload
skill-eval serve --reload

# The API will reload automatically when you edit files in skill_eval/api/
```

### Project Structure

```
skill_eval/
├── api/                     # FastAPI backend
│   ├── __init__.py
│   ├── main.py             # FastAPI app
│   ├── storage.py          # JSON file storage
│   └── routes/
│       ├── evals.py        # Eval endpoints
│       ├── runs.py         # Run endpoints
│       ├── skills.py       # Skills endpoints
│       └── config.py       # Config endpoints
└── ...

web/                         # React frontend
├── src/
│   ├── App.tsx             # Main app component
│   ├── index.css           # Global styles
│   └── main.tsx            # App entry point
├── package.json
└── vite.config.ts
```

## Authentication (Coming Soon)

GitHub OAuth will be added to enable authenticated features:

| Feature | Anonymous | Logged In |
|---------|-----------|-----------|
| View/edit local evals | ✅ | ✅ |
| Run evals (mock executor) | ✅ | ✅ |
| Run evals (copilot-sdk) | ❌ | ✅ |
| Scan GitHub repos for skills | ❌ | ✅ |
| LLM-assisted generation | ❌ | ✅ |

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
skill-eval serve --port 8080
```

### API Connection Errors

Make sure the API server is running:

```bash
curl http://localhost:8000/api/health
```

Should return:
```json
{"status": "ok", "version": "0.0.2"}
```

### CORS Errors

The API is configured to allow requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative port)

If you need to add more origins, edit `skill_eval/api/main.py`.

## Future Features

### Phase 3: Integration & Polish
- [ ] Docker + docker-compose setup
- [ ] GitHub OAuth authentication
- [ ] Dark/light mode toggle
- [ ] Keyboard shortcuts (⌘K command palette)
- [ ] Mobile responsive layout
- [ ] Eval editor with YAML syntax highlighting
- [ ] Real-time run viewer with SSE
- [ ] Skills browser with GitHub integration

## API Reference

For complete API documentation, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Contributing

Contributions to the Web UI are welcome! Areas of focus:

1. **UI/UX Improvements**: Better visualizations, animations, accessibility
2. **Feature Additions**: Eval editor, run viewer, settings page
3. **Authentication**: GitHub OAuth integration
4. **Testing**: Frontend tests with Vitest, API tests with pytest
5. **Docker**: Containerization for easy deployment

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
