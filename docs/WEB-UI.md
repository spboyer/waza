# Web UI Documentation

## Overview

The waza Web UI provides a modern dashboard for creating, editing, and running eval suites visually with real-time updates.

## Quick Start

### Starting the Web UI

```bash
# Install web dependencies (first time only)
pip install waza[web]

# Or install manually
pip install fastapi uvicorn[standard]

# Start the server
waza serve

# Custom port
waza serve --port 3000

# Development mode with auto-reload
waza serve --reload
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

All data is stored in `~/.waza/` as JSON and YAML files:

```
~/.waza/
├── config.json              # User preferences
├── evals/                   # Eval suite definitions
│   ├── my-waza.yaml
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
waza serve --reload

# The API will reload automatically when you edit files in waza/api/
```

### Project Structure

```
waza/
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
waza serve --port 8080
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

If you need to add more origins, edit `waza/api/main.py`.

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

## Complete Feature Set

### Enhanced Pages

#### Dashboard
- Overview metrics (Total Evals, Total Runs, Model, Executor)
- Quick actions (View All Evals, Configure Settings)
- Recent runs with status badges
- Eval suites preview with grid layout

#### Evals List
- Filterable table of eval suites
- Search by name or skill
- Run and Delete actions per eval
- Empty state with CLI hints

#### Run Details
- Real-time progress updates via SSE
- Status tracking (queued, running, completed, failed)
- Progress bar and task counters
- Results display with pass/fail badges
- Transcript viewer (conversation history)
- Error display for failed runs

#### Settings
- GitHub OAuth authentication status
- Login/Logout functionality
- Model configuration (Claude, GPT variants)
- Executor selection (mock or copilot-sdk)
- System information display

### Authentication

GitHub OAuth is now fully implemented:
- Login redirects to GitHub OAuth flow
- Session management with cookies
- Protected routes for copilot-sdk and advanced features
- User profile display in Settings

### Docker Deployment

The application is now containerized:

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access at http://localhost:8000
```

Environment variables for OAuth:
- `GITHUB_CLIENT_ID` - Your GitHub OAuth app client ID
- `GITHUB_CLIENT_SECRET` - Your GitHub OAuth app secret
- `GITHUB_REDIRECT_URI` - OAuth callback URL

See `.env.example` for configuration.

### Real-time Features

- Server-Sent Events (SSE) for live run updates
- Background task execution for eval runs
- Progress tracking with detailed status
- Automatic refetching for active runs

## Development Workflow

### Frontend Development

```bash
cd web/
npm install
npm run dev
```

The dev server runs on http://localhost:5173 with hot reload.

### Backend Development

```bash
waza serve --reload
```

The API server runs on http://localhost:8000 with auto-reload.

### Full Stack Development

Run both servers simultaneously:

```bash
# Terminal 1: Backend
waza serve --reload

# Terminal 2: Frontend  
cd web && npm run dev
```

Access:
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

