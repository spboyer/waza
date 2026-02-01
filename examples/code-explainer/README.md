# Code Explainer Eval

Example eval suite for the "code-explainer" skill that explains code snippets to users.

## The Skill

See [SKILL.md](./SKILL.md) for the full skill definition. This skill:
- Explains code snippets in plain language
- Provides step-by-step breakdowns
- Highlights key concepts and patterns

## Complete Workflow

This example demonstrates the full waza workflow:

### 1. View the Skill Definition

```bash
cat examples/code-explainer/SKILL.md
```

### 2. Generate an Eval (optional - already done here)

```bash
# Generate eval from SKILL.md
waza generate examples/code-explainer/SKILL.md -o ./my-code-explainer-eval

# Or with LLM assistance for better tasks
waza generate examples/code-explainer/SKILL.md -o ./my-code-explainer-eval --assist
```

### 3. Run the Eval

```bash
# Quick test with mock executor
waza run examples/code-explainer/eval.yaml \
  --executor mock \
  --context-dir examples/code-explainer/fixtures \
  -v

# Full test with Copilot SDK
waza run examples/code-explainer/eval.yaml \
  --executor copilot-sdk \
  --context-dir examples/code-explainer/fixtures \
  -v
```

## Structure

```
code-explainer/
├── SKILL.md                     # ⭐ Skill definition (source of truth)
├── eval.yaml                    # Main eval configuration
├── fixtures/                    # Code files to explain
│   ├── factorial.py             # Python recursion example
│   ├── fetch_user.js            # JavaScript async example
│   ├── squares.py               # Python list comprehension
│   └── user_orders.sql          # SQL JOIN example
├── tasks/                       # Individual test tasks
│   ├── explain-python-recursion.yaml
│   ├── explain-js-async.yaml
│   ├── explain-list-comprehension.yaml
│   └── explain-sql-join.yaml
├── graders/
│   └── explanation_quality.py   # Custom grader for explanation quality
└── trigger_tests.yaml           # Trigger accuracy tests
```

## What It Tests

This eval tests a code explanation skill across:

| Dimension | Coverage |
|-----------|----------|
| **Languages** | Python, JavaScript, SQL |
| **Concepts** | Recursion, async/await, list comprehensions, JOINs |
| **Complexity** | Beginner to intermediate |

## Metrics

| Metric | Weight | Threshold | What It Measures |
|--------|--------|-----------|------------------|
| `task_completion` | 40% | 80% | Did the skill complete the explanation? |
| `trigger_accuracy` | 30% | 90% | Does it trigger on appropriate prompts? |
| `behavior_quality` | 30% | 70% | Tool usage, response time within limits? |

## Graders

### Global Graders (in eval.yaml)
- **has_explanation**: Output length > 10 chars
- **no_errors**: No fatal error patterns in output

### Custom Grader (explanation_quality.py)
Evaluates explanations on 5 criteria (20 points each):
1. Sufficient length (≥200 chars)
2. Structured sections (overview, steps, key points)
3. Language identification
4. Educational tone
5. No error indicators

Pass threshold: 60%

## Customizing

### Add a New Task

Create `tasks/explain-new-concept.yaml`:

```yaml
id: explain-new-concept-001
name: Explain New Concept
description: Test explaining X concept

tags:
  - language
  - concept

inputs:
  prompt: |
    Explain this code:
    ```python
    # Your code here
    ```
  context:
    language: python
    complexity: beginner
    concept: your-concept

expected:
  output_contains:
    - "keyword1"
  outcomes:
    - type: task_completed

graders:
  - name: explains_concept
    type: code
    config:
      assertions:
        - "len(output) > 10"
```

### Modify Trigger Tests

Edit `trigger_tests.yaml` to add prompts that should or shouldn't trigger the skill.
