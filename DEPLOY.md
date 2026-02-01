# skill-eval Web UI - Docker Deployment

## Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/spboyer/evals-for-skills.git
cd evals-for-skills

# Build and run
docker-compose up -d

# Access the Web UI
open http://localhost:8000
```

## Configuration

### GitHub OAuth (Optional)

To enable authenticated features (copilot-sdk executor, skill scanning, LLM-assisted generation):

1. Create a GitHub OAuth App at https://github.com/settings/developers
2. Set the callback URL to `http://localhost:8000/api/auth/callback`
3. Copy `.env.example` to `.env` and add your credentials:

```bash
cp .env.example .env
# Edit .env with your GitHub OAuth credentials
```

4. Restart the container:

```bash
docker-compose down
docker-compose up -d
```

### Without OAuth

The Web UI works without GitHub OAuth for:
- Viewing and editing local evals
- Running evals with mock executor
- Viewing run history
- Basic configuration

## Data Persistence

Eval data is persisted in `~/.skill-eval/` on your host machine:

```
~/.skill-eval/
├── config.json          # User preferences
├── evals/               # Eval suite YAML files
├── runs/                # Run results and transcripts
└── cache/               # Temporary files
```

This directory is mounted as a volume in the Docker container.

## Services

The Docker Compose stack includes:

- **skill-eval**: FastAPI backend + React frontend
  - Port: 8000
  - Volumes: `~/.skill-eval` for data persistence
  - Environment: Optional GitHub OAuth credentials

## Logs

View logs:

```bash
docker-compose logs -f
```

## Stopping

```bash
docker-compose down
```

## Production Deployment

For production deployment:

1. Use a reverse proxy (nginx, Caddy) with HTTPS
2. Set proper OAuth redirect URI for your domain
3. Configure firewall rules
4. Use environment variables for secrets
5. Set up backup for `~/.skill-eval/`

Example nginx config:

```nginx
server {
    listen 443 ssl;
    server_name evals.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs
```

### Can't access Web UI

Verify the container is running:
```bash
docker-compose ps
```

Check port availability:
```bash
netstat -tuln | grep 8000
```

### OAuth not working

Verify environment variables:
```bash
docker-compose config
```

Ensure GitHub OAuth app callback URL matches your deployment URL.

## Development

To develop locally without Docker:

```bash
# Install dependencies
pip install -e ".[web]"
cd web && npm install

# Run backend
skill-eval serve --reload

# Run frontend (in another terminal)
cd web && npm run dev
```

See [docs/WEB-UI.md](docs/WEB-UI.md) for detailed development docs.
