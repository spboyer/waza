---
name: skill-eval-runner
description: |
  Run evaluations on Agent Skills to measure their effectiveness. 
  USE FOR: "run skill evals", "evaluate my skill", "test skill quality", 
  "check skill triggers", "skill compliance check", "measure skill performance",
  "run evals on [skill-name]", "grade skill execution".
  DO NOT USE FOR: writing skills (use skill-authoring), improving frontmatter 
  (use sensei), or general testing unrelated to skills.
metadata:
  author: spboyer
  version: "1.0"
---

# Skill Eval Runner

> Evaluate Agent Skills like you evaluate AI Agents

This skill runs evaluations on other skills to measure their effectiveness using the same patterns that power AI agent evaluations.

## When to Use

- Running quality evaluations on a skill
- Testing if a skill triggers on correct prompts
- Measuring skill behavior quality
- Generating eval reports for CI/CD

## Commands

### Run Evals
```
Run evals on <skill-name>
```

### Initialize Eval Suite
```
Create evals for <skill-name>
```

### Generate Report
```
Generate eval report for <skill-name>
```

## Workflow

1. **Check for Eval Suite**: Look for `eval.yaml` in the skill directory
2. **Load Tasks**: Parse task definitions from `tasks/*.yaml`
3. **Execute**: Run each task through the configured graders
4. **Report**: Output results in JSON or Markdown format

## Metrics Measured

| Metric | Description | Default Threshold |
|--------|-------------|-------------------|
| Task Completion | Did the skill accomplish the goal? | 80% |
| Trigger Accuracy | Was skill invoked on correct prompts? | 90% |
| Behavior Quality | Tool calls, efficiency, reasoning | 70% |

## Grader Types

- **Code Graders**: Deterministic assertions, regex matching
- **LLM Graders**: Model-as-judge with configurable rubrics
- **Human Graders**: Manual review workflow

## Example Usage

### Running Evals
```bash
# From CLI
skill-eval run ./my-skill/eval.yaml

# Output to file
skill-eval run ./my-skill/eval.yaml -o results.json
```

### Interpreting Results
```json
{
  "summary": {
    "pass_rate": 0.85,
    "composite_score": 0.82
  },
  "metrics": {
    "task_completion": { "score": 0.9, "passed": true },
    "trigger_accuracy": { "score": 0.95, "passed": true }
  }
}
```

## References

- [Eval Specification](references/EVAL-SPEC.md) - Full eval.yaml schema
- [Writing Tasks](references/WRITING-TASKS.md) - Task definition guide
- [Grader Reference](references/GRADERS.md) - Available graders
