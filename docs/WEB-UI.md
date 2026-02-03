# waza Web UI

The waza Web UI provides a visual dashboard for creating, running, and analyzing skill evaluations.

## Quick Start

```bash
# Install with web dependencies
pip install waza[web]

# Start the server
waza serve

# Open in browser
open http://localhost:8000
```

## Features

### Dashboard
- Overview of all evals and recent runs
- Quick stats: total evals, running, passed, failed
- Quick access to run evals

### Evals Management
- List all imported evaluations
- View eval details and task configurations
- Run evals with one click
- Delete unused evals

### Run Viewer
- Real-time progress during execution (SSE streaming)
- Pass/fail summary with percentages
- Expandable task results with:
  - Trial details and timing
  - Grader results
  - Conversation transcripts
- LLM-generated improvement suggestions

### Settings
- Configure default model
- Select executor (mock vs copilot-sdk)
- Theme preferences (light/dark)

## CLI Commands

```bash
# Start on default port (8000)
waza serve

# Custom port
waza serve --port 3000

# Development mode with hot reload
waza serve --reload

# Custom host (e.g., for network access)
waza serve --host 0.0.0.0
```

## Docker Deployment

### Using Docker Compose

```bash
# Start the service
docker-compose up

# With GitHub OAuth
GITHUB_CLIENT_ID=xxx GITHUB_CLIENT_SECRET=yyy docker-compose up
```

### Manual Docker Build

```bash
# Build image
docker build -t waza .

# Run container
docker run -p 8000:8000 -v waza-data:/data waza
```

## GitHub OAuth (Optional)

Enable GitHub OAuth to:
- Use the copilot-sdk executor (requires authentication)
- Persist user preferences

### Setup

1. Create a GitHub OAuth App: https://github.com/settings/applications/new
2. Set callback URL to: `http://localhost:8000/api/auth/callback`
3. Copy Client ID and Secret
4. Configure via environment:

```bash
export GITHUB_CLIENT_ID=your_client_id
export GITHUB_CLIENT_SECRET=your_client_secret
waza serve
```

Without OAuth configured, the Web UI still works but:
- Only mock executor is available
- Settings are stored locally

## API Endpoints

The Web UI is powered by a REST API:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/evals` | GET | List all evals |
| `/api/evals` | POST | Create/import eval |
| `/api/evals/{id}` | GET | Get eval details |
| `/api/evals/{id}` | DELETE | Delete eval |
| `/api/runs` | GET | List runs (optionally by eval_id) |
| `/api/runs` | POST | Start a new run |
| `/api/runs/{id}` | GET | Get run details |
| `/api/runs/{id}/stream` | GET | SSE stream for live progress |
| `/api/runs/{id}/stop` | POST | Stop a running eval |
| `/api/config` | GET | Get configuration |
| `/api/config` | PUT | Update configuration |
| `/api/auth/login` | GET | Start OAuth flow |
| `/api/auth/callback` | GET | OAuth callback |
| `/api/auth/logout` | POST | Logout |
| `/api/auth/user` | GET | Get current user |

## Data Storage

Evals and run results are stored in `~/.waza/`:

```
~/.waza/
├── evals/           # Eval YAML files
├── runs/            # Run results JSON
├── cache/           # Temporary cache
└── config.json      # User settings
```

Override with `WAZA_DATA_DIR` environment variable.

## Development

### Frontend Development

```bash
cd web
npm install
npm run dev    # Starts on http://localhost:5173
```

The Vite dev server proxies `/api` to the backend at `http://localhost:8000`.

### Backend Development

```bash
pip install -e ".[web,dev]"
waza serve --reload
```

### Running Both

In separate terminals:
```bash
# Terminal 1: Backend
waza serve --reload

# Terminal 2: Frontend
cd web && npm run dev
```

Access the frontend at `http://localhost:5173` for hot-reloading during development.

## Tech Stack

- **Backend**: FastAPI + uvicorn
- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **State**: React Query
- **Routing**: React Router
