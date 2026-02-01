# Agent Instructions for waza Repository

## Overview

This repository contains `waza`, a CLI tool for evaluating Agent Skills. When making changes, follow these guidelines to maintain consistency and quality.

## Copilot SDK Usage

**IMPORTANT:** The GitHub Copilot SDK package is `copilot`, NOT `copilot_sdk`.

### Correct Import Pattern

```python
# ✅ CORRECT - Use this pattern
from copilot import CopilotClient

# ❌ WRONG - This package doesn't exist
from copilot_sdk import create_session
```

### Standard SDK Usage Pattern

When using the Copilot SDK for LLM calls, follow this pattern (used in `generator.py`, `executors/copilot.py`, and `cli.py`):

```python
import asyncio
import contextlib
import tempfile
from copilot import CopilotClient

async def call_llm(prompt: str, model: str = "claude-sonnet-4-20250514") -> str:
    """Standard pattern for Copilot SDK LLM calls."""
    # Create temp workspace (required by SDK)
    workspace = tempfile.mkdtemp(prefix="waza-")
    
    # Initialize client
    client = CopilotClient({
        "cwd": workspace,
        "log_level": "error",
    })
    await client.start()
    
    try:
        # Create session
        session = await client.create_session({
            "model": model,
            "streaming": True,
        })
        
        # Collect response
        output_parts: list[str] = []
        done_event = asyncio.Event()
        
        def handle_event(event) -> None:
            event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)
            if event_type == "assistant.message":
                if hasattr(event.data, 'content') and event.data.content:
                    output_parts.append(event.data.content)
            elif event_type == "assistant.message_delta" and hasattr(event.data, 'delta_content') and event.data.delta_content:
                output_parts.append(event.data.delta_content)
            if event_type in ("session.idle", "session.error"):
                done_event.set()
        
        session.on(handle_event)
        await session.send({"prompt": prompt})
        
        # Wait for completion
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(done_event.wait(), timeout=120)
        
        # Cleanup session
        with contextlib.suppress(Exception):
            await session.destroy()
        
        return "".join(output_parts)
    finally:
        # Always cleanup client and workspace
        await client.stop()
        import shutil
        shutil.rmtree(workspace, ignore_errors=True)
```

### Key SDK Concepts

1. **CopilotClient** requires a `cwd` (working directory) - use temp directories
2. **Sessions** are created per-conversation with model config
3. **Events** are streamed - use event handlers to collect responses
4. **Event types**: `assistant.message`, `assistant.message_delta`, `session.idle`, `session.error`
5. **Always cleanup**: Stop client, destroy sessions, remove temp directories

### Fixture Isolation

Each task execution gets a **fresh temp workspace** with fixtures copied in:

1. Runner reads files from original `--context-dir` (fixtures folder)
2. Executor creates new temp workspace (e.g., `/tmp/waza-abc123/`)
3. Files copied into temp workspace
4. Agent works in temp workspace (edits happen here)
5. Temp workspace destroyed after task
6. Next task starts fresh with original fixtures

**The original fixtures directory is never modified.** This ensures task isolation.

## Documentation Requirements

**Always update documentation when making changes.** The following files must be kept in sync:

| File | Purpose | Update When |
|------|---------|-------------|
| `README.md` | Main project overview, CLI commands, examples | Any CLI change, new feature |
| `DEMO-SCRIPT.md` | Video demo walkthrough | New features, workflow changes, version bumps |
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

### DEMO-SCRIPT.md Maintenance

The demo script requires special attention because it contains **hardcoded values** that must be updated:

#### Version Bump Checklist
When releasing a new version, search and update these in `DEMO-SCRIPT.md`:

- [ ] **Install URL**: `waza-X.Y.Z-py3-none-any.whl` (Pre-Demo Setup section)
- [ ] **Expected output versions**: `waza vX.Y.Z` in all code block outputs
- [ ] **Download URLs**: Any GitHub release download links

#### Content Accuracy Checklist
After any rename or major change, verify:

- [ ] **Product name**: Search for old names (e.g., "skill-eval", "Skill-eval", "Skill Eval")
- [ ] **Package names**: Search for old package names (e.g., "skill_eval")
- [ ] **Repo URLs**: Verify all `github.com/...` URLs point to correct repo
- [ ] **Example paths**: Verify `examples/` paths match actual directory structure
- [ ] **CLI output examples**: Run actual commands and verify output matches docs
- [ ] **File structure examples**: Verify `tree` output matches actual structure

#### Quick Verification Commands
```bash
# Find version references
grep -n "waza-[0-9]" DEMO-SCRIPT.md
grep -n "waza v[0-9]" DEMO-SCRIPT.md

# Find potential old names (adjust pattern as needed)
grep -in "skill-eval\|skill_eval" DEMO-SCRIPT.md

# Verify example commands work
waza run examples/code-explainer/eval.yaml --executor mock -v
```

#### Common Mistakes to Avoid
1. **Forgetting expected output blocks** - These often have version strings embedded
2. **Mixed casing** - "Skill-eval" vs "skill-eval" vs "waza"
3. **Install URLs** - Often overlooked in setup sections
4. **Workflow file references** - `.github/workflows/` filenames

## Code Structure

```
waza/
├── cli.py              # CLI entrypoint (click commands)
├── runner.py           # Eval orchestration
├── generator.py        # SKILL.md → eval generation (includes AssistedGenerator)
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

### LLM-Assisted Generation

The `AssistedGenerator` class in `generator.py` uses Copilot SDK to generate better evals:

1. `generate_tasks()` - Asks LLM to create realistic test tasks
2. `generate_fixtures()` - Asks LLM for domain-appropriate fixture files  
3. `suggest_graders()` - Asks LLM for relevant graders/assertions

Falls back to pattern-based `EvalGenerator` if LLM fails.

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=waza

# Test CLI manually
waza --help
waza run examples/code-explainer/eval.yaml -v
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
# Pattern-based generation
waza generate <SKILL.md URL or path> -o ./my-eval

# LLM-assisted generation (better quality)
waza generate <SKILL.md URL or path> -o ./my-eval --assist --model claude-opus-4.5
```

### Run eval with all options
```bash
waza run ./eval.yaml \
  --executor copilot-sdk \
  --model claude-sonnet-4-20250514 \
  --context-dir ./fixtures \
  --log transcript.json \
  --output results.json \
  --suggestions-file suggestions.md \
  -v
```

### Key CLI flags
- `-v, --verbose` - Real-time conversation display
- `-o, --output` - Save results JSON
- `--log` - Save conversation transcript
- `--context-dir` - Project files for context
- `--executor` - mock or copilot-sdk
- `--model` - LLM model to use
- `--assist` - Use LLM for better task/fixture generation (generate command only)
- `--suggestions` - Get LLM-powered improvement suggestions for failed tasks (run command)
- `--suggestions-file` - Save suggestions to markdown file (implies --suggestions)
