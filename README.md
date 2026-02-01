# Skills Eval Framework

> Evaluate Agent Skills like you evaluate AI Agents

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

A framework for evaluating [Agent Skills](https://agentskills.io/specification) using the same patterns and metrics that power AI agent evaluations. Measure whether your skills accomplish their intended goals with structured, reproducible tests.

## Features

- 🎯 **Task Completion Metrics** - Did the skill accomplish the goal?
- 🔍 **Trigger Accuracy Testing** - Is the skill invoked on the right prompts?
- 📊 **Behavior Quality Analysis** - Tool calls, efficiency, reasoning patterns
- 🤖 **Multiple Grader Types** - Code-based, LLM-as-judge, human review
- 📈 **JSON Reports** - Machine-readable results aligned with agent eval standards
- 🔄 **CI/CD Ready** - Run in GitHub Actions or any CI pipeline
- 🧩 **Eval-as-Skill** - Meta-evaluation capability within skill runtimes
- 🔬 **Real Integration Testing** - Use Copilot SDK for actual LLM responses
- 📊 **Model Comparison** - Compare results across different models
- 📡 **Runtime Telemetry** - Capture and analyze production metrics

---

## Quick Start

### 1. Installation

```bash
# Basic installation
pip install skill-eval

# With LLM grading support (OpenAI/Anthropic)
pip install skill-eval[llm]

# With Copilot SDK for real integration tests
pip install skill-eval[copilot]

# Full installation (all features)
pip install skill-eval[all]
```

**From source (development):**
```bash
git clone https://github.com/spboyer/evals-for-skills.git
cd evals-for-skills
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Create Your First Eval

```bash
# Option A: Scaffold a blank eval suite
skill-eval init my-skill

# Option B: Auto-generate from a SKILL.md file
skill-eval generate https://raw.githubusercontent.com/org/repo/main/skills/my-skill/SKILL.md

# Option C: LLM-assisted generation (recommended for better tasks)
skill-eval generate ./SKILL.md --assist

# Option D: Init with SKILL.md integration
skill-eval init my-skill --from-skill ./path/to/SKILL.md

# This creates:
# my-skill/
# ├── eval.yaml           # Main eval configuration
# ├── trigger_tests.yaml  # Trigger accuracy tests
# ├── fixtures/           # Sample project files for context
# └── tasks/
#     └── example-task.yaml
```

### 3. Configure the Eval

Edit `my-skill/eval.yaml`:

```yaml
name: my-skill-eval
skill: my-skill
version: "1.0"

config:
  trials_per_task: 3        # Run each task 3 times for consistency
  timeout_seconds: 300      # 5 minute timeout per task
  executor: mock            # Use 'copilot-sdk' for real tests

metrics:
  - name: task_completion
    weight: 0.4
    threshold: 0.8          # 80% of tasks must complete

  - name: trigger_accuracy
    weight: 0.3
    threshold: 0.9          # 90% trigger accuracy required

  - name: behavior_quality
    weight: 0.3
    threshold: 0.7          # 70% behavior quality required

tasks:
  - "tasks/*.yaml"          # Include all task files
```

### 4. Run the Eval

```bash
# Run with mock executor (fast, no API calls)
skill-eval run my-skill/eval.yaml

# Run with verbose output (shows progress and details)
skill-eval run my-skill/eval.yaml -v

# Run with specific model
skill-eval run my-skill/eval.yaml --model gpt-4o

# Run with real Copilot SDK (requires authentication)
skill-eval run my-skill/eval.yaml --executor copilot-sdk

# Save results to file
skill-eval run my-skill/eval.yaml -o results.json
```

### 5. View Results

```
╭─────────────────── my-skill-eval ───────────────────╮
│ ✅ PASSED                                           │
│                                                     │
│ Pass Rate: 100.0% (4/4)                            │
│ Composite Score: 0.95                              │
│ Duration: 1234ms                                   │
╰─────────────────────────────────────────────────────╯

                  Metrics                   
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric           ┃ Score ┃ Threshold ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
│ task_completion  │  1.00 │      0.80 │ ✅     │
│ trigger_accuracy │  0.95 │      0.90 │ ✅     │
│ behavior_quality │  0.88 │      0.70 │ ✅     │
└──────────────────┴───────┴───────────┴────────┘
```

---

## Documentation

| Guide | Description |
|-------|-------------|
| **[Tutorial](docs/TUTORIAL.md)** | Step-by-step guide to writing skill evals |
| **[Grader Reference](docs/GRADERS.md)** | All 8 grader types with examples |
| **[Integration Testing](docs/INTEGRATION-TESTING.md)** | Using Copilot SDK for real tests |
| **[Telemetry Guide](docs/TELEMETRY.md)** | Capturing production metrics |
| **[Demo Script](DEMO-SCRIPT.md)** | Video demo walkthrough |

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `skill-eval run <eval.yaml>` | Run an evaluation suite |
| `skill-eval init <skill-name>` | Scaffold a new eval suite |
| `skill-eval generate <SKILL.md>` | Auto-generate eval from a SKILL.md file |
| `skill-eval compare <files...>` | Compare results across runs/models |
| `skill-eval analyze <telemetry>` | Analyze runtime telemetry |
| `skill-eval report <results.json>` | Generate reports from results |
| `skill-eval list-graders` | List available grader types |

### Common Options

```bash
# Run options
skill-eval run eval.yaml \
  --executor mock|copilot-sdk \       # Execution engine
  --model <model-name> \              # Model to use
  --output results.json \             # Save results
  --log transcript.json \             # Save full conversation transcript
  --context-dir ./my-project \        # Directory with project files for context
  --suggestions                       # Get LLM-powered improvement suggestions for failures
  --suggestions-file suggestions.md \ # Save suggestions to markdown file
  -v, --verbose                       # Show real-time conversation and details

# Init options
skill-eval init my-skill \
  --path ./evals \                    # Output directory
  --from-skill <SKILL.md>             # Generate from SKILL.md file or URL

# Generate options (auto-generate eval from SKILL.md)
skill-eval generate https://example.com/SKILL.md \
  --output ./my-skill-eval \          # Output directory
  --force                             # Overwrite existing files
  --assist                            # Use LLM for better task/fixture generation
  --model claude-sonnet-4-20250514    # Model for assisted generation

# Available models for --assist:
#   claude-sonnet-4-20250514 (default)
#   claude-opus-4.5
#   gpt-4o
#   gpt-5
```

---

## Concepts

This framework aligns with established agent evaluation patterns:

| Concept | Description |
|---------|-------------|
| **Task** | A single test case with inputs and success criteria |
| **Trial** | One execution attempt of a task (multiple trials for consistency) |
| **Grader** | Logic that scores an aspect of skill performance |
| **Transcript** | Full record of skill execution (tool calls, outputs) |
| **Outcome** | Final state after skill execution |
| **Eval Suite** | Collection of tasks for a specific skill |

---

## Writing Tasks

Tasks define individual test cases. Create YAML files in your `tasks/` directory:

```yaml
# tasks/deploy-app.yaml
id: deploy-app-001
name: Deploy Container App
description: Test deploying a container to Azure

# What to send to the skill
inputs:
  prompt: "Deploy my app to Azure Container Apps"
  context:
    files: ["Dockerfile", "app.py"]
    environment: production

# What we expect to happen
expected:
  # Keywords that should appear in output
  output_contains:
    - "container"
    - "deployed"
  
  # Required outcomes
  outcomes:
    - type: task_completed
  
  # Tool call requirements
  tool_calls:
    required:
      - pattern: "az containerapp"
    forbidden:
      - pattern: "rm -rf"
  
  # Behavior constraints
  behavior:
    max_tool_calls: 10
    max_response_time_ms: 30000

# Task-specific graders (optional)
graders:
  - name: validates_deployment
    type: code
    config:
      assertions:
        - "'success' in output.lower()"
```

---

## Grader Types

8 built-in graders for different validation needs:

| Type | Description | Use Case |
|------|-------------|----------|
| `code` | Python assertions | Exact validation logic |
| `regex` | Pattern matching | Output format checking |
| `semantic` | Embedding similarity | Meaning comparison |
| `llm` | LLM-as-judge | Nuanced quality assessment |
| `human` | Manual review | Complex judgments |
| `rubric` | Multi-criteria scoring | Structured evaluation |
| `tool-call` | Tool usage validation | Behavior checking |
| `custom` | External script | Custom logic |

See **[Grader Reference](docs/GRADERS.md)** for detailed examples.

---

## Eval Specification

The main `eval.yaml` file configures your evaluation suite:

```yaml
# eval.yaml
name: my-skill-eval
skill: my-skill
version: "1.0"

config:
  trials_per_task: 3
  timeout_seconds: 300
  executor: mock                    # or copilot-sdk for real tests
  model: claude-sonnet-4-20250514   # model for execution

metrics:
  - name: task_completion
    weight: 0.4
    threshold: 0.8
  - name: trigger_accuracy
    weight: 0.3
    threshold: 0.9
  - name: behavior_quality
    weight: 0.3
    threshold: 0.7

graders:
  - type: code
    name: output_validation
    script: graders/validate.py
  - type: llm
    name: quality_check
    rubric: graders/quality_rubric.md

tasks:
  - "tasks/*.yaml"   # Glob pattern for task files
```

---

## Executor Types

Choose how tasks are executed:

| Executor | Use Case | Requires | Speed |
|----------|----------|----------|-------|
| `mock` | Unit tests, CI/CD, development | Nothing | ⚡ Fast |
| `copilot-sdk` | Integration tests, benchmarking | Copilot auth | 🐢 Slower |

```bash
# Fast mock execution (default) - no API calls
skill-eval run eval.yaml

# Real Copilot SDK execution - actual LLM responses
skill-eval run eval.yaml --executor copilot-sdk --model gpt-4o
```

**Copilot SDK Setup:**
```bash
# Install with copilot support
pip install skill-eval[copilot]

# Authenticate (one-time)
copilot auth login

# Run integration tests
skill-eval run eval.yaml --executor copilot-sdk
```

See **[Integration Testing Guide](docs/INTEGRATION-TESTING.md)** for details.

---

## Model Comparison

Compare skill performance across different models:

```bash
# Run with different models
skill-eval run eval.yaml --model gpt-4o -o results-gpt4o.json
skill-eval run eval.yaml --model claude-sonnet-4-20250514 -o results-claude.json
skill-eval run eval.yaml --model gpt-4o-mini -o results-mini.json

# Generate comparison report
skill-eval compare results-*.json -o comparison.md
```

Output:
```
              Summary Comparison              
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Metric          ┃ gpt-4o ┃ claude  ┃ gpt-4o-mini ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━┩
│ Pass Rate       │ 100.0% │  95.0%  │      85.0%  │
│ Composite Score │   0.98 │   0.92  │        0.81 │
└─────────────────┴────────┴─────────┴─────────────┘

🏆 Best: gpt-4o (score: 0.98)
```

---

## Results Format

Results are saved as JSON for programmatic use:

```json
{
  "eval_id": "my-skill-eval-20260131",
  "skill": "my-skill",
  "config": {
    "model": "claude-sonnet-4-20250514",
    "executor": "copilot-sdk",
    "trials_per_task": 3
  },
  "summary": {
    "total_tasks": 10,
    "passed": 8,
    "failed": 2,
    "pass_rate": 0.8,
    "composite_score": 0.82
  },
  "metrics": {
    "task_completion": { "score": 0.85, "passed": true },
    "trigger_accuracy": { "score": 0.95, "passed": true }
  }
}
```

---

## Runtime Telemetry

Capture metrics from skills running in production:

```bash
# Analyze telemetry files
skill-eval analyze telemetry/sessions.json

# Filter to specific skill
skill-eval analyze telemetry/ --skill azure-deploy -o analysis.json
```

See [Telemetry Guide](docs/TELEMETRY.md) for integration patterns.

---

## GitHub Actions

Add skill evals to your CI/CD pipeline:

```yaml
# .github/workflows/skill-eval.yaml
name: Skill Evaluation

on:
  pull_request:
    paths:
      - 'skills/**'
      - 'evals/**'

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install skill-eval
        run: pip install skill-eval
      
      - name: Run evaluations
        run: |
          skill-eval run evals/my-skill/eval.yaml \
            --output results.json
      
      - name: Check thresholds
        run: |
          # Fail if composite score < 0.8
          python -c "
          import json
          r = json.load(open('results.json'))
          score = r['summary']['composite_score']
          assert score >= 0.8, f'Score {score} below threshold'
          "
      
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: eval-results
          path: results.json
```

---

## Examples

The repository includes a sample eval suite:

| Example | Description |
|---------|-------------|
| [`code-explainer`](examples/code-explainer/) | Demo skill with 4 code explanation tasks |

Run the example:
```bash
skill-eval run examples/code-explainer/eval.yaml
```

### Generating Evals from SKILL.md

You can auto-generate eval suites from any skill that follows the [Agent Skills specification](https://agentskills.io/specification):

```bash
# Generate from a URL (e.g., GitHub raw file)
skill-eval generate https://raw.githubusercontent.com/microsoft/GitHub-Copilot-for-Azure/main/plugin/skills/azure-functions/SKILL.md

# Generate from a local file  
skill-eval generate ./my-skill/SKILL.md -o ./evals/my-skill

# The generator creates:
# - eval.yaml with graders and metrics
# - trigger_tests.yaml with activation tests
# - tasks/ with example task files
# - fixtures/ with sample project files for context
```

### Using Project Context

When running evals, provide real project files for more realistic testing:

```bash
# Use generated fixtures as default for all tasks
skill-eval run ./my-eval/eval.yaml --context-dir ./my-eval/fixtures

# Use your own project
skill-eval run ./my-eval/eval.yaml --context-dir ~/projects/my-app

# With verbose output to see the conversation
skill-eval run ./my-eval/eval.yaml --context-dir ./fixtures -v

# Save conversation transcript for debugging
skill-eval run ./my-eval/eval.yaml --log ./transcript.json
```

Tasks can also specify their own `context_dir` to override the global setting:

```yaml
# tasks/deploy-functions.yaml
id: deploy-functions-001
context_dir: ./fixtures/functions-project  # Task-specific override

inputs:
  prompt: "Deploy my Azure Function"
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

---

## References

- [Anthropic - Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Agent Skills Specification](https://agentskills.io/specification)
- [OpenAI Evals](https://github.com/openai/evals)
- [Anthropic Skills Best Practices](https://support.anthropic.com/en/articles/12512198-how-to-create-custom-skills)

## License

MIT
