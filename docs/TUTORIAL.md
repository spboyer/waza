# Writing Skill Evals - Tutorial

This tutorial walks you through creating evaluations for your Agent Skills.

## Prerequisites

- Python 3.11+
- `waza` installed:
  ```bash
  # From GitHub releases (recommended)
  pip install https://github.com/spboyer/waza/releases/latest/download/waza-0.1.0-py3-none-any.whl
  
  # Or from PyPI when available
  pip install waza
  ```
- An existing skill to evaluate

## Step 1: Initialize Your Eval Suite

You have several options to create your eval suite:

### Option A: Auto-Generate from SKILL.md (Recommended)

The fastest way to get started is to generate from an existing SKILL.md:

```bash
# Generate eval from a SKILL.md URL
waza generate https://raw.githubusercontent.com/microsoft/GitHub-Copilot-for-Azure/main/plugin/skills/azure-functions/SKILL.md -o ./azure-functions-eval

# Or from a local file
waza generate ./path/to/SKILL.md -o ./my-waza

# The generator creates:
# my-waza/
# ├── eval.yaml           # Main eval configuration
# ├── trigger_tests.yaml  # Trigger accuracy tests  
# ├── tasks/              # Generated task definitions
# │   ├── task-001.yaml
# │   ├── task-002.yaml
# │   └── task-003.yaml
# └── fixtures/           # Sample project files for context
#     ├── function_app.py
#     ├── host.json
#     └── requirements.txt
```

### Option A+ : LLM-Assisted Generation (Best Quality)

For more realistic and comprehensive test cases, use LLM-assisted generation:

```bash
# Use --assist to have an LLM analyze the skill and generate better tests
waza generate ./SKILL.md -o ./my-waza --assist

# Specify a different model if desired
waza generate ./SKILL.md -o ./my-waza --assist --model gpt-4o

# Available models: claude-sonnet-4-20250514 (default), claude-opus-4.5, gpt-4o, gpt-5
```

LLM-assisted generation:
- Creates more natural, realistic user prompts
- Generates domain-appropriate fixture files
- Suggests relevant graders and assertions
- Produces 5 diverse tasks testing different scenarios
- Falls back to pattern-based generation if LLM fails

### Option B: Blank Scaffold
```bash
# Create eval scaffolding from scratch
waza init my-awesome-skill

# This creates:
# my-awesome-skill/
# ├── eval.yaml           # Main eval configuration
# ├── trigger_tests.yaml  # Trigger accuracy tests
# ├── tasks/
# │   └── example-task.yaml
# └── graders/
#     └── custom_grader.py
```

### Option C: Init with SKILL.md Integration
```bash
# Scaffold AND generate from SKILL.md in one step
waza init my-skill --from-skill ./path/to/SKILL.md
```

## Step 2: Configure Your Eval Specification

Edit `eval.yaml` to define your evaluation:

```yaml
name: my-awesome-waza
description: Evaluate the my-awesome-skill skill
skill: my-awesome-skill
version: "1.0"

config:
  trials_per_task: 3      # Run each task 3 times for consistency
  timeout_seconds: 300    # 5 minute timeout per trial
  parallel: true          # Run tasks concurrently

metrics:
  - name: task_completion
    weight: 0.4           # 40% of composite score
    threshold: 0.8        # Must achieve 80% to pass
  
  - name: trigger_accuracy
    weight: 0.3
    threshold: 0.9        # 90% trigger accuracy required
  
  - name: behavior_quality
    weight: 0.3
    threshold: 0.7

graders:
  - type: code
    name: basic_validation
    config:
      assertions:
        - "len(output) > 0"
        - "'error' not in output.lower()"

tasks:
  - "tasks/*.yaml"
```

## Step 3: Write Task Definitions

Tasks are individual test cases. Create them in `tasks/`:

```yaml
# tasks/deploy-app.yaml
id: deploy-app-001
name: Deploy Simple App
description: Test deploying a basic application

# Task-specific context directory (overrides global --context-dir)
context_dir: ./fixtures/web-app

inputs:
  prompt: "Deploy this app to Azure"
  context:
    project_type: "web-app"
    language: "python"
  files:
    - path: app.py
      content: |
        from flask import Flask
        app = Flask(__name__)

expected:
  outcomes:
    - type: deployment_initiated
  
  tool_calls:
    required:
      - pattern: "azd|az"
    forbidden:
      - pattern: "rm -rf"
  
  behavior:
    max_tool_calls: 20
  
  output_contains:
    - "deploy"
    - "success"

graders:
  - name: deployment_check
    type: code
    assertions:
      - "'deployed' in output.lower() or 'success' in output.lower()"
```

## Step 4: Define Trigger Tests

Test when your skill should (and shouldn't) activate:

```yaml
# trigger_tests.yaml
skill: my-awesome-skill

should_trigger_prompts:
  - prompt: "Use my-awesome-skill to do X"
    reason: "Explicit skill mention"
  
  - prompt: "Help me with [relevant task]"
    reason: "Matches skill domain"

should_not_trigger_prompts:
  - prompt: "What's the weather like?"
    reason: "Completely unrelated"
  
  - prompt: "Help with [different domain]"
    reason: "Wrong skill for this task"
```

## Step 5: Choose Your Graders

### Code Grader (Deterministic)
```yaml
- type: code
  name: output_check
  config:
    assertions:
      - "len(output) > 0"
      - "'success' in output.lower()"
      - "len(errors) == 0"
```

### Regex Grader (Pattern Matching)
```yaml
- type: regex
  name: format_check
  config:
    must_match:
      - "deployed to .+"
      - "https?://.+"
    must_not_match:
      - "error|failed|exception"
```

### LLM Grader (AI Judge)
```yaml
- type: llm
  name: quality_assessment
  model: gpt-4o-mini
  rubric: |
    Score the response 1-5 on:
    1. Correctness: Did it do the right thing?
    2. Completeness: Did it address all requirements?
    3. Clarity: Was the response clear and helpful?
    
    Return JSON: {"score": N, "reasoning": "...", "passed": true/false}
```

### Script Grader (Custom Logic)
```yaml
- type: script
  name: custom_validation
  config:
    script: graders/custom_grader.py
```

## Step 6: Run Your Evals

```bash
# Run all tasks
waza run my-awesome-skill/eval.yaml

# Run with verbose output (shows real-time conversation)
waza run my-awesome-skill/eval.yaml -v

# Run with project context (use fixtures or your own project)
waza run my-awesome-skill/eval.yaml --context-dir ./my-awesome-skill/fixtures

# Save conversation transcript for debugging
waza run my-awesome-skill/eval.yaml --log transcript.json

# Full debugging run
waza run my-awesome-skill/eval.yaml -v --context-dir ./fixtures --log transcript.json -o results.json

# Run specific task
waza run my-awesome-skill/eval.yaml --task deploy-app-001

# Output to file
waza run my-awesome-skill/eval.yaml -o results.json

# Override trials
waza run my-awesome-skill/eval.yaml --trials 5

# Set fail threshold
waza run my-awesome-skill/eval.yaml --fail-threshold 0.9

# Run with real Copilot SDK (requires auth)
waza run my-awesome-skill/eval.yaml --executor copilot-sdk

# Get LLM suggestions for failed tasks (displays on screen)
waza run my-awesome-skill/eval.yaml --suggestions

# Save suggestions to markdown file (also displays on screen)
waza run my-awesome-skill/eval.yaml --suggestions-file suggestions.md
```

### Progress Output

By default, the CLI shows a progress bar during execution:

```
Progress: ████████████░░░░░░░░░░░░░░░░░░ 4/10 (40%)
Running: Deploy Simple App (trial 2/3)
```

Use `-v/--verbose` for real-time conversation display:

```
⠋ Running evaluation...
  Task: Deploy Simple App [Trial 1/3]
    Prompt: Help me deploy my application
    Response: I'll help you deploy using Azure...
    Tool: azure-deploy (2 calls)
  Task: Deploy Simple App [Trial 2/3]
    ...
```

### Conversation Transcript Logging

Save the full conversation transcript for detailed debugging:

```bash
waza run eval.yaml --log transcript.json -v
```

The transcript includes timestamps, task/trial info, and full message content:

```json
[
  {
    "timestamp": "2025-01-20T10:30:00Z",
    "task": "deploy-app-001",
    "trial": 1,
    "role": "user",
    "content": "Help me deploy my application"
  },
  {
    "timestamp": "2025-01-20T10:30:01Z",
    "task": "deploy-app-001",
    "trial": 1,
    "role": "assistant",
    "content": "I'll help you deploy using Azure..."
  }
]
```

### Using Project Context

The `--context-dir` option provides project files to the skill:

```bash
# Use generated fixtures as default for all tasks
waza run my-skill/eval.yaml --context-dir ./my-skill/fixtures

# Use your real project
waza run my-skill/eval.yaml --context-dir ~/projects/my-app
```

Individual tasks can override the global context with their own `context_dir`:

```yaml
# tasks/deploy-app.yaml
id: deploy-app-001
name: Deploy Web App
context_dir: ./fixtures/web-app  # Task-specific, overrides --context-dir

inputs:
  prompt: "Deploy this web app"
```

This gives the skill real code to work with, making tests more realistic.

## Step 7: Interpret Results

### Console Output
```
╭─────────────────── my-awesome-waza ───────────────────╮
│ ✅ PASSED                                                    │
│                                                              │
│ Pass Rate: 85.0% (17/20)                                     │
│ Composite Score: 0.82                                        │
│ Duration: 45000ms                                            │
╰──────────────────────────────────────────────────────────────╯
```

### JSON Output Structure
```json
{
  "eval_id": "my-awesome-waza-20260131-001",
  "skill": "my-awesome-skill",
  "summary": {
    "total_tasks": 20,
    "passed": 17,
    "failed": 3,
    "pass_rate": 0.85,
    "composite_score": 0.82
  },
  "metrics": {
    "task_completion": { "score": 0.9, "passed": true },
    "trigger_accuracy": { "score": 0.95, "passed": true },
    "behavior_quality": { "score": 0.78, "passed": true }
  },
  "tasks": [...]
}
```

## Step 8: Integrate with CI/CD

Add to your GitHub Actions workflow:

```yaml
- name: Run Skill Evals
  run: |
    pip install waza
    waza run ./my-skill/eval.yaml \
      --output results.json \
      --fail-threshold 0.8
```

Or use the reusable workflow:

```yaml
jobs:
  eval:
    uses: your-org/waza/.github/workflows/waza.yaml@main
    with:
      eval-path: ./my-skill/eval.yaml
      fail-threshold: 0.8
```

## Best Practices

1. **Start Simple**: Begin with basic code graders, add LLM graders later
2. **Multiple Trials**: Use 3+ trials for consistent results
3. **Clear Triggers**: Define explicit trigger phrases in your skill description
4. **Anti-Triggers**: Test what SHOULDN'T trigger your skill
5. **Incremental Testing**: Add tasks as you find edge cases
6. **Track Baselines**: Store results to detect regressions

## Troubleshooting

### "No tasks found"
- Check your `tasks` glob pattern in eval.yaml
- Ensure task files have `.yaml` extension

### "Grader failed"
- Check assertion syntax (Python expressions)
- Verify context variables are available

### "Low trigger accuracy"
- Improve your skill's `description` field
- Add more explicit trigger phrases

## Next Steps

- Read the [Grader Reference](GRADERS.md)
- See [Example Evals](../examples/)
- Join the discussion on improving skill evals
