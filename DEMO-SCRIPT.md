# Demo Script: Skill Evals Framework

> A step-by-step walkthrough for creating a demo video of the skill-eval framework.

## Demo Overview

**Duration:** ~12-15 minutes  
**Goal:** Show how to evaluate Agent Skills using the same patterns as AI agent evals

---

## Pre-Demo Setup

```bash
# Ensure clean environment
cd ~/demo
rm -rf skill-eval-demo
mkdir skill-eval-demo && cd skill-eval-demo

# Create a virtual environment
uv venv && source .venv/bin/activate

# Install skill-eval (with Copilot SDK support for advanced demo)
uv pip install skill-eval[copilot]
```

---

## Part 1: Introduction (1 min)

### Talking Points

> "Today I'm going to show you **skill-eval** — a framework for evaluating Agent Skills using the same patterns that power AI agent evaluations."

> "Just like we have evals for AI agents, we now have evals for skills. This helps answer: Did the skill accomplish what we wanted?"

### Show the Version

```bash
skill-eval --version
# Output: skill-eval, version 0.1.0
```

### Show Available Commands

```bash
skill-eval --help
```

**Expected Output:**
```
Usage: skill-eval [OPTIONS] COMMAND [ARGS]...

  Skill Eval - Evaluate Agent Skills like you evaluate AI Agents.

Commands:
  analyze       Analyze runtime telemetry data.
  compare       Compare results across multiple eval runs.
  generate      Generate eval suite from a SKILL.md file.
  init          Initialize a new eval suite for a skill.
  list-graders  List available grader types.
  report        Generate a report from eval results.
  run           Run an evaluation suite.
```

> "Notice we have seven commands including the new **generate** command for auto-creating evals from SKILL.md files."

---

## Part 2: Generate Eval from SKILL.md (2 min) ⭐ NEW

### Talking Points

> "The fastest way to create an eval is to generate it from an existing SKILL.md file. Let's try it with Azure Functions."

### Generate from URL

```bash
skill-eval generate https://raw.githubusercontent.com/microsoft/GitHub-Copilot-for-Azure/main/plugin/skills/azure-functions/SKILL.md \
  -o azure-functions-eval
```

**Expected Output:**
```
skill-eval v0.1.0

Parsing: https://raw.githubusercontent.com/microsoft/...
✓ Parsed skill: azure-functions
  Description: Build and deploy serverless Azure Functions...
  Triggers extracted: 15
  Anti-triggers: 4
  Keywords: 20

✓ Created eval.yaml
✓ Created trigger_tests.yaml
✓ Created tasks/task-001.yaml
✓ Created tasks/task-002.yaml
✓ Created tasks/task-003.yaml
✓ Created fixtures/function_app.py
✓ Created fixtures/host.json
✓ Created fixtures/requirements.txt
✓ Created fixtures/local.settings.json

╭─────────────────── ✓ Success ───────────────────╮
│ Generated eval suite at: azure-functions-eval   │
│                                                 │
│ Run with:                                       │
│   skill-eval run azure-functions-eval/eval.yaml │
╰─────────────────────────────────────────────────╯
```

### Explore the Generated Structure

```bash
tree azure-functions-eval
```

**Expected:**
```
azure-functions-eval/
├── eval.yaml
├── fixtures/
│   ├── function_app.py
│   ├── host.json
│   ├── local.settings.json
│   └── requirements.txt
├── tasks/
│   ├── task-001.yaml
│   ├── task-002.yaml
│   └── task-003.yaml
└── trigger_tests.yaml
```

> "Notice it created **fixtures/** with sample Azure Functions code. This gives the skill real context to work with."

---

## Part 2b: LLM-Assisted Generation (2 min) ⭐ NEW

### Talking Points

> "For even better test cases, we can use the `--assist` flag to have an LLM analyze the SKILL.md and generate more realistic tasks and fixtures."

### Generate with LLM Assistance

```bash
skill-eval generate https://raw.githubusercontent.com/microsoft/GitHub-Copilot-for-Azure/main/plugin/skills/azure-functions/SKILL.md \
  -o azure-functions-eval-assisted \
  --assist

# Use a different model (claude-opus-4.5, gpt-4o, gpt-5)
skill-eval generate ./SKILL.md -o ./my-eval --assist --model claude-opus-4.5
```

**Expected Output:**
```
skill-eval v0.1.0

Parsing: https://raw.githubusercontent.com/microsoft/...
✓ Parsed skill: azure-functions
  Description: Build and deploy serverless Azure Functions...

Using LLM-assisted generation with claude-sonnet-4-20250514...

⠋ Generating tasks...
✓ Generated 5 tasks
⠋ Generating fixtures...
✓ Generated 4 fixtures
⠋ Suggesting graders...
✓ Suggested 3 graders

✓ Created tasks/task-001.yaml (Deploy HTTP Trigger Function)
✓ Created tasks/task-002.yaml (Create Timer-based Function)
✓ Created tasks/task-003.yaml (Debug Cold Start Issues)
✓ Created tasks/task-004.yaml (Configure Function App Settings)
✓ Created tasks/task-005.yaml (Set Up CI/CD for Functions)
✓ Created fixtures/function_app.py
✓ Created fixtures/host.json
✓ Created fixtures/local.settings.json
✓ Created fixtures/requirements.txt
✓ Created eval.yaml
✓ Created trigger_tests.yaml

╭────────────────────── ✓ Success ──────────────────────╮
│ Generated eval suite at: azure-functions-eval-assisted │
│                                                        │
│ Run with:                                              │
│   skill-eval run azure-functions-eval-assisted/eval.yaml │
╰────────────────────────────────────────────────────────╯
```

### Compare the Tasks

```bash
# Pattern-based task
cat azure-functions-eval/tasks/task-001.yaml

# LLM-generated task (more realistic prompt)
cat azure-functions-eval-assisted/tasks/task-001.yaml
```

> "Notice how the LLM-generated tasks have more natural, realistic prompts like 'Deploy my HTTP trigger function to Azure' instead of just 'Deploy my function to Azure'."

> "The --assist flag is great for creating comprehensive test suites quickly."

---

## Part 3: Initialize from Scratch (2 min)

### Talking Points

> "You can also create an eval suite from scratch. Let's create one for a 'code-reviewer' skill."

### Run Init Command

```bash
skill-eval init code-reviewer
```

**Expected Output:**
```
✓ Created eval suite at: code-reviewer

Structure created:
  code-reviewer/
  ├── eval.yaml
  ├── trigger_tests.yaml
  ├── tasks/
  │   └── example-task.yaml
  └── graders/
      └── custom_grader.py

Next steps:
  1. Edit tasks/*.yaml to add test cases
  2. Edit trigger_tests.yaml for trigger accuracy tests
  3. Run: skill-eval run code-reviewer/eval.yaml
```

### Show the Eval Spec

```bash
cat code-reviewer/eval.yaml
```

**Highlight:**
- `trials_per_task: 3` — Multiple runs for consistency
- Three metrics: task_completion (40%), trigger_accuracy (30%), behavior_quality (30%)
- Configurable thresholds — fail the eval if quality drops

---

## Part 3: Customize Task Definitions (2 min)

### Talking Points

> "Tasks are individual test cases. Let's create a real task for our code reviewer skill."

### Create a Task File

```bash
cat > code-reviewer/tasks/review-python-code.yaml << 'EOF'
# Review Python Code Task
id: review-python-001
name: Review Python Function
description: Test reviewing a Python function for issues

inputs:
  prompt: "Review this Python code for issues"
  context:
    language: "python"
  files:
    - path: example.py
      content: |
        def calculate_total(items):
            total = 0
            for i in range(len(items)):
                total = total + items[i]['price']
            return total

expected:
  output_contains:
    - "review"
  
  behavior:
    max_tool_calls: 10

graders:
  - name: found_issues
    type: code
    assertions:
      - "len(output) > 50"
      - "'improve' in output.lower() or 'suggest' in output.lower() or 'issue' in output.lower()"
EOF
```

### Show the Task

```bash
cat code-reviewer/tasks/review-python-code.yaml
```

**Highlight:**
- `inputs`: The prompt and context
- `expected`: What success looks like
- `graders`: How to score the result

---

## Part 4: Define Trigger Tests (1 min)

### Talking Points

> "Trigger accuracy tests whether your skill activates on the right prompts — and stays quiet on the wrong ones."

### Update Trigger Tests

```bash
cat > code-reviewer/trigger_tests.yaml << 'EOF'
# Trigger accuracy tests for code-reviewer
skill: code-reviewer

should_trigger_prompts:
  - prompt: "Review this code"
    reason: "Explicit review request"
  
  - prompt: "Check my Python function for bugs"
    reason: "Bug checking is code review"
  
  - prompt: "What's wrong with this implementation?"
    reason: "Asking about code issues"

should_not_trigger_prompts:
  - prompt: "What time is it?"
    reason: "Unrelated question"
  
  - prompt: "Deploy my app to Azure"
    reason: "Deployment, not review"
  
  - prompt: "Write me a Python script"
    reason: "Code writing, not reviewing"
EOF
```

---

## Part 5: Run the Eval with Verbose Output (2 min) ⭐ NEW

### Talking Points

> "Now let's run the evaluation. I'll use verbose mode to see the conversation in real-time."

### Execute the Eval

```bash
skill-eval run code-reviewer/eval.yaml -v
```

**Expected Output (verbose shows real-time conversation):**
```
skill-eval v0.1.0

✓ Loaded eval: code-reviewer-eval
  Skill: code-reviewer
  Executor: mock
  Model: claude-sonnet-4-20250514
  Tasks: 2
  Trials per task: 3

⠋ Running evaluation...
  Task: Example Task [Trial 1/3]
    Prompt: Tell me about this codebase
    Response: This is a mock response...
  Task: Example Task [Trial 2/3]
    ...

╭────────────────────────── code-reviewer-eval ──────────────────────────╮
│ ✅ PASSED                                                               │
│                                                                         │
│ Pass Rate: 100.0% (2/2)                                                 │
│ Composite Score: 1.00                                                   │
│ Duration: 5ms                                                           │
╰─────────────────────────────────────────────────────────────────────────╯

                     Metrics                     
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric           ┃ Score ┃ Threshold ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
│ task_completion  │  1.00 │      0.80 │ ✅     │
│ trigger_accuracy │  1.00 │      0.90 │ ✅     │
│ behavior_quality │  1.00 │      0.70 │ ✅     │
└──────────────────┴───────┴───────────┴────────┘
```

> "Verbose mode shows you the conversation as it happens - great for debugging!"

### Run with Project Context

```bash
# Use fixtures (generated code files) as context
skill-eval run azure-functions-eval/eval.yaml --context-dir azure-functions-eval/fixtures -v
```

> "The --context-dir option provides real project files to the skill, so it has something to work with."

### Save Conversation Transcript

```bash
skill-eval run azure-functions-eval/eval.yaml \
  --context-dir azure-functions-eval/fixtures \
  --log transcript.json \
  --output results.json
```

> "The --log flag saves the full conversation transcript for debugging. The --output saves results."

### View Transcript

```bash
cat transcript.json | python -m json.tool | head -30
```

**Expected:**
```json
[
  {
    "timestamp": "2025-01-20T10:30:00Z",
    "task": "deploy-function-001",
    "trial": 1,
    "role": "user",
    "content": "Help me create an Azure Function..."
  },
  {
    "timestamp": "2025-01-20T10:30:01Z",
    "task": "deploy-function-001",
    "trial": 1,
    "role": "assistant", 
    "content": "I'll help you create an Azure Function..."
  }
]
```

### Save Results to JSON

```bash
skill-eval run code-reviewer/eval.yaml --output results.json

# View the JSON structure
cat results.json | python -m json.tool | head -40
```

**Highlight:**
- `config`: Shows model and executor used
- `summary`: Overall pass rate and composite score
- `metrics`: Individual metric scores
- `tasks`: Per-task breakdown

---

## Part 6: Show Different Grader Types (1 min)

### Talking Points

> "Skill-eval supports multiple grader types, just like agent evals."

### List Graders

```bash
skill-eval list-graders
```

**Expected Output:**
```
Available Grader Types

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Type              ┃ Description                           ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ code              │ Deterministic code-based assertions   │
│ regex             │ Pattern matching against output       │
│ tool_calls        │ Validate tool call patterns           │
│ script            │ Run external Python script            │
│ llm               │ LLM-as-judge with rubric              │
│ llm_comparison    │ Compare output to reference using LLM │
│ human             │ Requires human review                 │
│ human_calibration │ Human calibration for LLM graders     │
└───────────────────┴───────────────────────────────────────┘
```

**Highlight:**
- **Code graders**: Fast, deterministic, for CI/CD
- **LLM graders**: AI judge for quality assessment
- **Human graders**: Manual review workflow

---

## Part 7: Run an Existing Example (1 min)

### Talking Points

> "Let me show you a more complete example — evaluating the azure-deploy skill."

### Run Azure Deploy Eval

```bash
# Clone the examples (or copy from repo)
cd /path/to/evals-for-skills

skill-eval run examples/azure-deploy/eval.yaml
```

**Show the output with real tasks.**

---

## Part 8: Model Comparison (1.5 min) ⭐ NEW

### Talking Points

> "One of the most powerful features is comparing how your skill performs across different models."

### Run with Different Models

```bash
# Run with GPT-4o
skill-eval run examples/azure-deploy/eval.yaml --model gpt-4o -o results-gpt4o.json

# Run with Claude
skill-eval run examples/azure-deploy/eval.yaml --model claude-sonnet-4-20250514 -o results-claude.json
```

### Compare Results

```bash
skill-eval compare results-gpt4o.json results-claude.json
```

**Expected Output:**
```
Model Comparison Report

              Summary Comparison              
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Metric          ┃ gpt-4o ┃ claude-sonnet-4 ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Pass Rate       │ 100.0% │          100.0% │
│ Composite Score │   1.00 │            1.00 │
│ Tasks Passed    │    2/2 │             2/2 │
│ Duration        │  203ms │           202ms │
│ Executor        │   mock │            mock │
└─────────────────┴────────┴─────────────────┘

                  Per-Task Comparison                   
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Task                     ┃ gpt-4o  ┃ claude-sonnet-4 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ deploy-container-app-001 │ ✅ 1.00 │     ✅ 1.00     │
│ deploy-function-app-001  │ ✅ 1.00 │     ✅ 1.00     │
└──────────────────────────┴─────────┴─────────────────┘

🏆 Best: gpt-4o (score: 1.00)
```

> "This is incredibly useful for benchmarking and deciding which model works best for your skill."

---

## Part 9: Real Integration Testing (1 min) ⭐ NEW

### Talking Points

> "For real integration tests, you can use the Copilot SDK executor to get actual LLM responses."

### Show Executor Options

```bash
skill-eval run --help | grep executor
```

### Run with Copilot SDK (requires auth)

```bash
# This uses real Copilot SDK - requires authentication
skill-eval run examples/azure-deploy/eval.yaml \
  --executor copilot-sdk \
  --model claude-sonnet-4-20250514
```

> "The mock executor is perfect for CI/CD and fast iteration. The copilot-sdk executor is for real integration testing."

---

## Part 10: CI/CD Integration (30 sec)

### Talking Points

> "Skill evals integrate directly into your CI/CD pipeline."

### Show GitHub Actions Workflow

```bash
cat .github/workflows/skill-eval.yaml
```

**Highlight:**
- Reusable workflow
- Configurable thresholds
- Outputs for downstream jobs

---

## Part 11: Summary (30 sec)

### Talking Points

> "To recap what we've seen:"

1. **Generate** an eval suite from SKILL.md with `skill-eval generate`
2. **Initialize** from scratch with `skill-eval init`
3. **Define tasks** — individual test cases with fixtures
4. **Define triggers** — when should your skill activate?
5. **Choose graders** — code, LLM, or human
6. **Run evals** — with `-v` for real-time conversation, `--context-dir` for project files
7. **Debug** — save transcripts with `--log` for detailed analysis
8. **Compare models** — benchmark across different LLMs
9. **Get results** — JSON reports aligned with agent eval standards

> "Skills are becoming as important as agents. Now we can evaluate them with the same rigor."

---

## Bonus: Quick Reference Commands

```bash
# Initialize new eval suite
skill-eval init my-skill

# Generate eval from SKILL.md
skill-eval generate https://example.com/skills/SKILL.md -o ./my-eval

# Generate with LLM assistance (better tasks/fixtures)
skill-eval generate https://example.com/skills/SKILL.md -o ./my-eval --assist --model claude-opus-4.5

# Run evaluation (basic)
skill-eval run my-skill/eval.yaml

# Run with verbose output (see conversation)
skill-eval run my-skill/eval.yaml -v

# Run with project context (from fixtures or real project)
skill-eval run my-skill/eval.yaml --context-dir ./my-skill/fixtures

# Run with JSON output
skill-eval run my-skill/eval.yaml -o results.json

# Run with conversation transcript logging
skill-eval run my-skill/eval.yaml --log transcript.json

# Run with LLM suggestions for failures (displays and saves)
skill-eval run my-skill/eval.yaml --suggestions --suggestions-file suggestions.md

# Full debugging run with suggestions
skill-eval run my-skill/eval.yaml -v --context-dir ./fixtures --log transcript.json -o results.json --suggestions-file suggestions.md

# Run specific task
skill-eval run my-skill/eval.yaml --task task-id

# Override trials
skill-eval run my-skill/eval.yaml --trials 5

# Set fail threshold
skill-eval run my-skill/eval.yaml --fail-threshold 0.9

# Run with specific model
skill-eval run my-skill/eval.yaml --model gpt-4o

# Run with Copilot SDK (real integration)
skill-eval run my-skill/eval.yaml --executor copilot-sdk

# Compare results across models
skill-eval compare results-gpt4o.json results-claude.json -o comparison.md

# Analyze runtime telemetry
skill-eval analyze telemetry.json --skill azure-deploy

# Generate report from results
skill-eval report results.json --format markdown

# List available graders
skill-eval list-graders
```

---

## Demo Cleanup

```bash
# Remove demo directory
cd ~
rm -rf skill-eval-demo
```

---

## Key Messages for Demo

1. **"Evals for skills, just like evals for agents"** — Same patterns, same rigor
2. **"Auto-generate from SKILL.md"** — Get started in seconds with `skill-eval generate`
3. **"Fixtures for realistic testing"** — Generated project files give context
4. **"Three core metrics"** — Task completion, trigger accuracy, behavior quality
5. **"Multiple grader types"** — From deterministic to AI-powered
6. **"Real-time verbose output"** — See the conversation as it happens
7. **"Conversation logging"** — Debug with full transcript via `--log`
8. **"Model comparison"** — Benchmark skills across different LLMs
9. **"Two executor modes"** — Mock for CI/CD, Copilot SDK for real tests
10. **"CI/CD ready"** — Integrate into your pipeline

---

## Appendix: Troubleshooting During Demo

### If `skill-eval` command not found
```bash
pip install -e /path/to/evals-for-skills
```

### If tasks not loading
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('eval.yaml'))"
```

### If results look wrong
```bash
# Run with verbose
skill-eval run eval.yaml -v
```
