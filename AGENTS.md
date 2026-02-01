# Agent Instructions for skill-eval Repository

## Overview

This repository contains `skill-eval`, a CLI tool for evaluating Agent Skills. When making changes, follow these guidelines to maintain consistency and quality.

## Documentation Requirements

**Always update documentation when making changes.** The following files must be kept in sync:

| File | Purpose | Update When |
|------|---------|-------------|
| `README.md` | Main project overview, CLI commands, examples | Any CLI change, new feature |
| `DEMO-SCRIPT.md` | Video demo walkthrough | New features, workflow changes |
| `docs/TUTORIAL.md` | Step-by-step user guide | New features, config options |
| `docs/GRADERS.md` | Grader types reference | New grader types |
| `docs/INTEGRATION-TESTING.md` | Copilot SDK usage | Executor changes, auth changes |
| `docs/TELEMETRY.md` | Telemetry/metrics docs | New metrics, output changes |

### Documentation Checklist

When adding a new CLI option:
- [ ] Update `README.md` CLI commands table
- [ ] Update `README.md` common options section
- [ ] Update `DEMO-SCRIPT.md` quick reference commands
- [ ] Update `docs/TUTORIAL.md` relevant sections
- [ ] Add example usage in appropriate docs

When adding a new feature:
- [ ] Update `README.md` with feature overview
- [ ] Add section to `DEMO-SCRIPT.md` if demo-worthy
- [ ] Add step-by-step in `docs/TUTORIAL.md`
- [ ] Update any affected reference docs

## Code Structure

```
skill_eval/
├── cli.py              # CLI entrypoint (click commands)
├── runner.py           # Eval orchestration
├── generator.py        # SKILL.md → eval generation
├── schemas/
│   ├── eval_spec.py    # EvalSpec model
│   └── task.py         # Task model
├── executors/
│   ├── base.py         # BaseExecutor interface
│   ├── copilot.py      # Copilot SDK executor
│   └── mock.py         # Mock executor for testing
├── graders/            # Grader implementations
└── reporters/          # Output formatters
```

## Key Patterns

### Adding CLI Options

1. Add option to `cli.py` command decorator
2. Pass through to runner/executor as needed
3. Add validation in CLI if required
4. Update all docs (see checklist above)

### Adding Task Fields

1. Add field to `Task` model in `schemas/task.py`
2. Handle in `runner.py` `_run_trial()` method
3. Update task YAML examples in docs
4. Add to generated tasks in `generator.py` if applicable

### Adding Executor Features

1. Update `BaseExecutor` interface if needed
2. Implement in `CopilotExecutor` and `MockExecutor`
3. Update `docs/INTEGRATION-TESTING.md`

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=skill_eval

# Test CLI manually
skill-eval --help
skill-eval run examples/code-explainer/eval.yaml -v
```

## Commit Messages

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `chore:` Maintenance tasks
- `refactor:` Code restructuring

## Files to Ignore

These are generated/temporary and should not be committed:
- `transcript.json` - Conversation logs
- `results.json` - Eval results
- `azure-functions-eval/` - Generated test eval
- `.venv/` - Virtual environment
- `__pycache__/` - Python cache

## Quick Reference

### Generate eval from SKILL.md
```bash
skill-eval generate <SKILL.md URL or path> -o ./my-eval
```

### Run eval with all options
```bash
skill-eval run ./eval.yaml \
  --executor copilot-sdk \
  --model claude-sonnet-4-20250514 \
  --context-dir ./fixtures \
  --log transcript.json \
  --output results.json \
  -v
```

### Key CLI flags
- `-v, --verbose` - Real-time conversation display
- `-o, --output` - Save results JSON
- `--log` - Save conversation transcript
- `--context-dir` - Project files for context
- `--executor` - mock or copilot-sdk
- `--model` - LLM model to use
