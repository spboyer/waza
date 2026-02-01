# skill-eval Web UI

React + TypeScript frontend for the skill-eval Web UI dashboard.

## Quick Start

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development

The dev server runs on `http://localhost:5173` and expects the API backend on `http://localhost:8000`.

### Starting Both Servers

```bash
# Terminal 1: Start API backend
cd ..
skill-eval serve

# Terminal 2: Start frontend dev server
cd web
npm run dev
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **ESLint** - Code linting

## Project Structure

```
src/
├── App.tsx          # Main app component
├── App.css          # Component styles
├── index.css        # Global styles (Tailwind)
└── main.tsx         # App entry point
```

## Building for Production

```bash
npm run build
```

The production build will be in the `dist/` directory. The API server can serve these static files.

## API Integration

The frontend communicates with the FastAPI backend via REST endpoints:

- `GET /api/evals` - List eval suites
- `GET /api/config` - Get configuration
- `POST /api/runs` - Start a new run
- etc.

See `../docs/WEB-UI.md` for complete API documentation.
