# Demo Script: waza

> Step-by-step walkthrough for demonstrating the waza framework.

## Demo Overview

**Duration:** ~12-15 minutes  
**Goal:** Show how to evaluate Agent Skills with the same rigor as AI agent evals

---

## Pre-Demo Setup

```bash
# Clean environment
cd ~/demo && rm -rf waza-demo
mkdir waza-demo && cd waza-demo

# Install waza
uv venv && source .venv/bin/activate
uv pip install "https://github.com/spboyer/waza/releases/latest/download/waza-0.1.0-py3-none-any.whl"
```

---

## Part 1: Introduction (1 min)

### The Hook

> "Agent Skills are becoming as important as the agents themselves. But how do you know if a skill actually works? How do you catch regressions? How do you compare performance across models?"

> "Today I'll show you **waza** — a framework that brings the same evaluation rigor we use for AI agents to Agent Skills."

### The Problem

> "Right now, testing skills is mostly manual. You try a prompt, eyeball the result, and hope it works in production. That doesn't scale."

> "waza fixes this with:"
> - **Automated test suites** generated from SKILL.md files
> - **Multiple grader types** — from simple regex to LLM-as-judge
> - **Model comparison** — benchmark skills across GPT-4, Claude, etc.
> - **CI/CD integration** — catch regressions before they ship

### Quick Demo

```bash
waza --version
waza --help
```

**Key commands:**
- `generate` — Create eval from SKILL.md
- `run` — Execute evaluation
- `compare` — Benchmark across models

---

## Part 2: Generate Eval from SKILL.md (2 min) ⭐ NEW

### Talking Points

> "The fastest way to create an eval is to generate it from an existing SKILL.md file. Let's try it with Azure Functions."

### Generate from URL

```bash
waza generate https://raw.githubusercontent.com/microsoft/GitHub-Copilot-for-Azure/main/plugin/skills/azure-functions/SKILL.md \
  -o azure-functions-eval
```

**Expected Output:**
```
waza v0.1.0

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
│   waza run azure-functions-eval/eval.yaml │
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
waza generate https://raw.githubusercontent.com/microsoft/GitHub-Copilot-for-Azure/main/plugin/skills/azure-functions/SKILL.md \
  -o azure-functions-eval-assisted \
  --assist

# Use a different model (claude-opus-4.5, gpt-4o, gpt-5)
waza generate ./SKILL.md -o ./my-eval --assist --model claude-opus-4.5
```

**Expected Output:**
```
waza v0.1.0

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
│   waza run azure-functions-eval-assisted/eval.yaml │
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

## Part 2c: Skill Discovery from Repos (2 min) ⭐ NEW

### Talking Points

> "What if you want to generate evals for ALL skills in a repository? waza can scan GitHub repos or local directories to discover skills automatically."

### Scan a GitHub Repository

```bash
# Interactive mode - select which skills to generate
waza generate --repo microsoft/GitHub-Copilot-for-Azure
```

**Expected Output:**
```
waza v0.2.0

Scanning microsoft/GitHub-Copilot-for-Azure for skills...
✓ Found 15 skills

Select skills to generate evals for:
  ◉ azure-functions          Azure Functions development
  ◯ azure-prepare            Prepare apps for Azure deployment
  ◉ azure-nodejs-production  Node.js production configuration
  ... (↑↓ to move, space to select, enter to confirm)

Use LLM-assisted generation? [Y/n]: y
Output directory [./evals]: 

Generating evals...
✓ azure-functions-eval created
✓ azure-nodejs-production-eval created
```

### Generate a Specific Skill (Recommended)

```bash
# Target a specific skill by name - no prompts, no long URLs
waza generate --repo microsoft/GitHub-Copilot-for-Azure --skill azure-functions -o ./eval
```

> "The `--skill` flag lets you target a specific skill without needing the full raw GitHub URL. Much cleaner!"

### Batch Mode (CI-Friendly)

```bash
# Generate all skills without prompts
waza generate --repo microsoft/GitHub-Copilot-for-Azure --all --output ./evals
```

> "The `--all` flag skips all prompts, perfect for CI/CD pipelines."

### Scan Local Directory

```bash
# Scan current directory for SKILL.md files
waza generate --scan
```

---

## Part 3: Initialize from Scratch (2 min)

### Talking Points

> "You can also create an eval suite from scratch. Let's create one for a 'code-reviewer' skill."

### Run Init Command

```bash
waza init code-reviewer
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
  ├── fixtures/
  │   └── example.py
  └── graders/
      └── custom_grader.py

Next steps:
  1. Add code files to fixtures/
  2. Edit tasks/*.yaml to add test cases
  3. Edit trigger_tests.yaml for trigger accuracy tests
  4. Run: waza run code-reviewer/eval.yaml --context-dir code-reviewer/fixtures
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

## Part 3b: Customize Task Definitions (2 min)

### Talking Points

> "Tasks are individual test cases. Let's create a real task for our code reviewer skill."

### Create a Fixture File First

```bash
# Create fixtures directory
mkdir -p code-reviewer/fixtures

# Create a code file to review
cat > code-reviewer/fixtures/example.py << 'EOF'
def calculate_total(items):
    total = 0
    for i in range(len(items)):
        total = total + items[i]['price']
    return total
EOF
```

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

expected:
  output_contains:
    - "review"
  
  behavior:
    max_tool_calls: 10

graders:
  - name: found_issues
    type: code
    config:
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
- `inputs.files.path`: Filename only — resolved via `--context-dir` at runtime
- `expected`: What success looks like
- `graders`: How to score the result

> "The `path: example.py` is relative to whatever you pass as `--context-dir`. There's no default — you must specify it when running."

### Run with Fixtures

```bash
# The --context-dir tells waza where to find the files
waza run code-reviewer/eval.yaml \
  --context-dir code-reviewer/fixtures \
  --executor mock \
  -v
```

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
waza run code-reviewer/eval.yaml -v
```

**Expected Output (verbose shows real-time conversation):**
```
waza v0.1.0

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
# Use fixtures (code files) as context
waza run examples/code-explainer/eval.yaml \
  --context-dir examples/code-explainer/fixtures \
  -v
```

> "The --context-dir option provides real project files to the skill, so it has something to work with."

### Save Conversation Transcript

```bash
waza run examples/code-explainer/eval.yaml \
  --context-dir examples/code-explainer/fixtures \
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
    "task": "explain-python-recursion-001",
    "trial": 1,
    "role": "user",
    "content": "Explain this code to me"
  },
  {
    "timestamp": "2025-01-20T10:30:01Z",
    "task": "explain-python-recursion-001",
    "trial": 1,
    "role": "assistant", 
    "content": "This Python function calculates the factorial..."
  }
]
```

### Save Results to JSON

```bash
waza run code-reviewer/eval.yaml --output results.json

# View the JSON structure
cat results.json | python -m json.tool | head -40
```

**Highlight:**
- `config`: Shows model and executor used
- `summary`: Overall pass rate and composite score
- `metrics`: Individual metric scores
- `tasks`: Per-task breakdown

---

## Part 5b: GitHub Issue Creation (1 min) ⭐ NEW

### Talking Points

> "After running an eval, you can automatically create GitHub issues with the results. This is great for tracking skill quality over time."

### Post-Run Issue Creation

```bash
# Run eval - prompts to create issues at the end
waza run ./eval.yaml --executor copilot-sdk
```

**At completion:**
```
╭─────────────────── azure-nodejs-production-eval ───────────────────╮
│ ❌ FAILED                                                          │
│ Pass Rate: 60.0% (3/5)                                             │
╰────────────────────────────────────────────────────────────────────╯

Create GitHub issues with results? [y/N]: y
Target repository [microsoft/GitHub-Copilot-for-Azure]: 
Create issues for: [F]ailed only, [A]ll skills, [N]one: f

Creating issues...
✓ Created issue #142: [Eval] azure-nodejs-production: 2 tasks failed
  → https://github.com/microsoft/GitHub-Copilot-for-Azure/issues/142
```

### Skip Prompts in CI

```bash
# Skip issue creation prompt (CI-friendly)
waza run ./eval.yaml --no-issues
```

> "The `--no-issues` flag is essential for CI pipelines where you don't want interactive prompts."

---

## Part 6: Show Different Grader Types (1 min)

### Talking Points

> "waza supports multiple grader types, just like agent evals."

### List Graders

```bash
waza list-graders
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

## Part 7: Run the Built-in Example (1 min)

### Talking Points

> "Let me show you a complete example — the code-explainer eval. This includes a SKILL.md, so you can see the full workflow."

### View the Skill Definition

```bash
# The example includes a complete SKILL.md
cat examples/code-explainer/SKILL.md | head -30
```

> "Every eval starts with a SKILL.md that defines what the skill does, when it should trigger, and how it should behave."

### Run Code Explainer Eval

```bash
# From the waza repo
cd /path/to/waza

# Run with mock executor and fixtures
waza run examples/code-explainer/eval.yaml \
  --executor mock \
  --context-dir examples/code-explainer/fixtures \
  -v
```

**Expected Output:**
```
waza v0.1.0

✓ Loaded eval: code-explainer-eval
  Skill: code-explainer
  Context: examples/code-explainer/fixtures (4 files)
  Executor: mock
  Model: claude-sonnet-4-20250514
  Tasks: 4
  Trials per task: 3

   Progress: ██████████████████████████████ 4/4 (100%)

╭──────────────────────── code-explainer-eval ────────────────────────╮
│ ✅ PASSED                                                           │
│                                                                     │
│ Pass Rate: 100.0% (4/4)                                             │
│ Composite Score: 1.00                                               │
│ Duration: 1230ms                                                    │
╰─────────────────────────────────────────────────────────────────────╯

                         Metrics                          
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Metric           ┃ Score ┃ Threshold ┃ Weight ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ task_completion  │  1.00 │      0.80 │    0.4 │ ✅     │
│ trigger_accuracy │  1.00 │      0.90 │    0.3 │ ✅     │
│ behavior_quality │  1.00 │      0.70 │    0.3 │ ✅     │
└──────────────────┴───────┴───────────┴────────┴────────┘

                               Task Results                                
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Task                           ┃ Status ┃ Score ┃ Duration ┃ Tool Calls ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Explain SQL JOIN Query         │ ✅     │  1.00 │    101ms │          2 │
│ Explain List Comprehension     │ ✅     │  1.00 │    102ms │          2 │
│ Explain JavaScript Async/Await │ ✅     │  1.00 │    102ms │          2 │
│ Explain Python Recursion       │ ✅     │  1.00 │    102ms │          2 │
└────────────────────────────────┴────────┴───────┴──────────┴────────────┘
```

### Explore the Example Structure

```bash
tree examples/code-explainer
```

**Structure:**
```
code-explainer/
├── SKILL.md                 # ⭐ Skill definition (source of truth)
├── eval.yaml                # Main eval config
├── fixtures/                # Code files the skill will explain
│   ├── factorial.py         # Python recursion
│   ├── fetch_user.js        # JavaScript async/await
│   ├── squares.py           # List comprehension
│   └── user_orders.sql      # SQL JOIN
├── tasks/                   # Test tasks
│   ├── explain-python-recursion.yaml
│   ├── explain-js-async.yaml
│   ├── explain-list-comprehension.yaml
│   └── explain-sql-join.yaml
├── graders/
│   └── explanation_quality.py  # Custom grader
└── trigger_tests.yaml       # Trigger accuracy tests
```

> "Notice it includes a SKILL.md — this is what you'd generate an eval from. The fixtures directory has real code files for context."

---

## Part 8: Model Comparison (1.5 min) ⭐ NEW

### Talking Points

> "One of the most powerful features is comparing how your skill performs across different models."

### Run with Different Models

```bash
# Run with GPT-4o
waza run examples/code-explainer/eval.yaml \
  --context-dir examples/code-explainer/fixtures \
  --model gpt-4o \
  -o results-gpt4o.json

# Run with Claude
waza run examples/code-explainer/eval.yaml \
  --context-dir examples/code-explainer/fixtures \
  --model claude-sonnet-4-20250514 \
  -o results-claude.json
```

### Compare Results

```bash
waza compare results-gpt4o.json results-claude.json
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
│ Tasks Passed    │    4/4 │             4/4 │
│ Duration        │  403ms │           401ms │
│ Executor        │   mock │            mock │
└─────────────────┴────────┴─────────────────┘

                      Per-Task Comparison                       
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Task                           ┃ gpt-4o  ┃ claude-sonnet-4 ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Explain SQL JOIN Query         │ ✅ 1.00 │     ✅ 1.00     │
│ Explain List Comprehension     │ ✅ 1.00 │     ✅ 1.00     │
│ Explain JavaScript Async/Await │ ✅ 1.00 │     ✅ 1.00     │
│ Explain Python Recursion       │ ✅ 1.00 │     ✅ 1.00     │
└────────────────────────────────┴─────────┴─────────────────┘

🏆 Best: gpt-4o (score: 1.00)
```

> "This is incredibly useful for benchmarking and deciding which model works best for your skill."

---

## Part 9: Real Integration Testing (1 min) ⭐ NEW

### Talking Points

> "For real integration tests, you can use the Copilot SDK executor to get actual LLM responses."

### Show Executor Options

```bash
waza run --help | grep executor
```

### Run with Copilot SDK (requires auth)

```bash
# This uses real Copilot SDK - requires authentication
waza run examples/code-explainer/eval.yaml \
  --executor copilot-sdk \
  --context-dir examples/code-explainer/fixtures \
  --model claude-sonnet-4-20250514 \
  -v
```

> "The mock executor is perfect for CI/CD and fast iteration. The copilot-sdk executor is for real integration testing."

---

## Part 10: CI/CD Integration (30 sec)

### Talking Points

> "Skill evals integrate directly into your CI/CD pipeline."

### Show GitHub Actions Workflow

```bash
cat .github/workflows/waza.yaml
```

**Highlight:**
- Reusable workflow
- Configurable thresholds
- Outputs for downstream jobs

---

## Part 11: Summary (30 sec)

### Talking Points

> "To recap what we've seen:"

1. **Discover skills** — scan GitHub repos or local directories with `--repo` and `--scan`
2. **Generate** an eval suite from SKILL.md with `waza generate --assist` for LLM help
3. **Initialize** from scratch with `waza init`
4. **Define tasks** — individual test cases with fixtures
5. **Define triggers** — when should your skill activate?
6. **Choose graders** — code, LLM, or human
7. **Run evals** — with `-v` for real-time conversation, `--context-dir` for project files
8. **Debug** — save transcripts with `--log` for detailed analysis
9. **Track issues** — create GitHub issues for failed tasks automatically
10. **Compare models** — benchmark across different LLMs
11. **Get results** — JSON reports aligned with agent eval standards

> "Skills are becoming as important as agents. Now we can evaluate them with the same rigor."

---

## Bonus: Quick Reference Commands

```bash
# Initialize new eval suite
waza init my-skill

# Generate eval from SKILL.md
waza generate https://example.com/skills/SKILL.md -o ./my-eval

# Generate with LLM assistance (better tasks/fixtures)
waza generate https://example.com/skills/SKILL.md -o ./my-eval --assist --model claude-opus-4.5

# Discover skills in a GitHub repo (interactive)
waza generate --repo microsoft/GitHub-Copilot-for-Azure

# Generate eval for a specific skill (recommended - no long URLs!)
waza generate --repo microsoft/GitHub-Copilot-for-Azure --skill azure-functions -o ./eval

# Discover and generate all skills (CI-friendly)
waza generate --repo microsoft/GitHub-Copilot-for-Azure --all --output ./evals

# Scan local directory for skills
waza generate --scan

# Run evaluation (basic)
waza run my-skill/eval.yaml

# Run with verbose output (see conversation)
waza run my-skill/eval.yaml -v

# Run with project context (from fixtures or real project)
waza run my-skill/eval.yaml --context-dir ./my-skill/fixtures

# Run with JSON output
waza run my-skill/eval.yaml -o results.json

# Run with conversation transcript logging
waza run my-skill/eval.yaml --log transcript.json

# Run with LLM suggestions for failures (displays and saves)
waza run my-skill/eval.yaml --suggestions --suggestions-file suggestions.md

# Skip GitHub issue creation prompt (CI-friendly)
waza run my-skill/eval.yaml --no-issues

# Full debugging run with suggestions
waza run my-skill/eval.yaml -v --context-dir ./fixtures --log transcript.json -o results.json --suggestions-file suggestions.md

# Run specific task
waza run my-skill/eval.yaml --task task-id

# Override trials
waza run my-skill/eval.yaml --trials 5

# Set fail threshold
waza run my-skill/eval.yaml --fail-threshold 0.9

# Run with specific model
waza run my-skill/eval.yaml --model gpt-4o

# Run with Copilot SDK (real integration)
waza run my-skill/eval.yaml --executor copilot-sdk

# Compare results across models
waza compare results-gpt4o.json results-claude.json -o comparison.md

# Analyze runtime telemetry
waza analyze telemetry.json --skill code-explainer

# Generate report from results
waza report results.json --format markdown

# List available graders
waza list-graders
```

---

## Demo Cleanup

```bash
# Remove demo directory
cd ~
rm -rf waza-demo
```

---

## Key Messages for Demo

1. **"Evals for skills, just like evals for agents"** — Same patterns, same rigor
2. **"Auto-generate from SKILL.md"** — Get started in seconds with `waza generate`
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

### If `waza` command not found
```bash
pip install -e /path/to/waza
```

### If tasks not loading
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('eval.yaml'))"
```

### If results look wrong
```bash
# Run with verbose
waza run eval.yaml -v
```
