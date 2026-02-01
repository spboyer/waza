# Grader Reference

Complete reference for all available grader types in waza.

## Overview

Graders evaluate skill execution and produce scores. Each grader returns:
- `score`: 0.0 to 1.0
- `passed`: boolean
- `message`: human-readable result
- `details`: additional metadata

## Inline vs Script Graders

Graders can be defined in two ways:

### Inline Graders (in eval.yaml or task files)

Best for simple validation logic that fits in YAML:

```yaml
graders:
  - type: code
    name: basic_check
    config:
      assertions:
        - "len(output) > 10"
        - "'success' in output.lower()"
  
  - type: regex
    name: format_check
    config:
      must_match:
        - "deployed to .+"
```

### Script Graders (in graders/ directory)

Best for complex, multi-criteria evaluation logic:

```
my-waza/
├── eval.yaml
├── tasks/
└── graders/
    └── quality_checker.py    # Complex custom logic
```

Reference in eval.yaml:
```yaml
graders:
  - type: script
    name: quality_checker
    config:
      script: graders/quality_checker.py
```

**When to use script graders:**
- Multi-criteria scoring (5+ checks)
- Domain-specific business logic
- Reusable across multiple evals
- Complex pattern matching or analysis
- Integration with external services

See the [code-explainer example](../examples/code-explainer/graders/explanation_quality.py) for a complete script grader implementation.

---

## Code Graders

### `code` - Assertion-Based Grader

Evaluates Python expressions against the execution context.

```yaml
- type: code
  name: my_grader
  config:
    assertions:
      - "len(output) > 0"
      - "'success' in output.lower()"
      - "len(errors) == 0"
```

**Available Context Variables:**
| Variable | Type | Description |
|----------|------|-------------|
| `output` | str | Final skill output |
| `outcome` | dict | Outcome state |
| `transcript` | list | Full execution transcript |
| `tool_calls` | list | Tool calls from transcript |
| `errors` | list | Errors from transcript |
| `duration_ms` | int | Execution duration |

**Available Functions:**
`len`, `any`, `all`, `str`, `int`, `float`, `bool`, `list`, `dict`, `re` (regex module)

**Scoring:** `passed_assertions / total_assertions`

**⚠️ Important:** Do NOT use generator expressions in assertions. They don't work with Python's `eval()` in restricted scope.

```yaml
# ❌ WRONG - generator expressions fail
assertions:
  - "any(kw in output for kw in ['azure', 'deploy'])"

# ✅ CORRECT - use explicit or chains
assertions:
  - "'azure' in output.lower() or 'deploy' in output.lower()"
```

---

### `regex` - Pattern Matching Grader

Matches output against regex patterns.

```yaml
- type: regex
  name: format_checker
  config:
    must_match:
      - "deployed to https?://.+"
      - "Resource group: .+"
    must_not_match:
      - "error|failed|exception"
      - "permission denied"
```

**Options:**
| Option | Type | Description |
|--------|------|-------------|
| `must_match` | list[str] | Patterns that MUST appear |
| `must_not_match` | list[str] | Patterns that MUST NOT appear |

**Scoring:** `passed_checks / total_checks`

---

### `tool_calls` - Tool Usage Grader

Validates which tools were called and how.

```yaml
- type: tool_calls
  name: tool_validator
  config:
    required:
      - pattern: "azd up"
      - pattern: "git commit"
    forbidden:
      - pattern: "rm -rf"
      - pattern: "sudo"
    max_calls: 20
```

**Options:**
| Option | Type | Description |
|--------|------|-------------|
| `required` | list | Patterns that MUST appear in tool calls |
| `forbidden` | list | Patterns that MUST NOT appear |
| `max_calls` | int | Maximum allowed tool calls |

---

### `script` - External Script Grader

Runs a custom Python script for complex validation.

```yaml
- type: script
  name: custom_logic
  config:
    script: graders/my_grader.py
```

**Script Format:**
```python
#!/usr/bin/env python3
import json
import sys

def grade(context: dict) -> dict:
    output = context.get("output", "")
    
    # Your custom logic here
    score = 1.0 if "success" in output else 0.0
    
    return {
        "score": score,
        "passed": score >= 0.5,
        "message": "Custom grading complete",
        "details": {"custom_field": "value"}
    }

if __name__ == "__main__":
    context = json.load(sys.stdin)
    print(json.dumps(grade(context)))
```

---

## LLM Graders

### `llm` - LLM-as-Judge Grader

Uses an AI model to evaluate quality.

```yaml
- type: llm
  name: quality_judge
  model: gpt-4o-mini
  rubric: |
    Score the skill execution from 1-5:
    
    1. Correctness: Did it accomplish the task?
    2. Completeness: Were all requirements addressed?
    3. Quality: Was the approach appropriate?
    
    Return JSON: {"score": N, "reasoning": "...", "passed": true/false}
```

**Options:**
| Option | Type | Description |
|--------|------|-------------|
| `model` | str | Model to use (default: gpt-4o-mini) |
| `rubric` | str | Evaluation rubric (inline or file path) |
| `threshold` | float | Pass threshold (default: 0.75) |

**Score Normalization:** Raw scores 1-5 are normalized to 0-1:
- Score 1 → 0.0
- Score 3 → 0.5
- Score 5 → 1.0

---

### `llm_comparison` - Reference Comparison Grader

Compares output against a reference using LLM.

```yaml
- type: llm_comparison
  name: reference_check
  model: gpt-4o-mini
  config:
    reference: |
      Expected output should include:
      - Confirmation of deployment
      - URL of deployed resource
      - Next steps for the user
```

---

## Human Graders

### `human` - Manual Review Grader

Marks tasks for human review.

```yaml
- type: human
  name: expert_review
  config:
    instructions: "Review for security best practices"
    criteria:
      - "Uses managed identity"
      - "No hardcoded secrets"
      - "Follows least privilege"
```

**Output:** Returns `pending` status until human submits review.

---

### `human_calibration` - Calibration Grader

Collects human labels to calibrate LLM graders.

```yaml
- type: human_calibration
  name: calibrate_quality
  config:
    calibrate_grader: quality_judge
```

---

## Task-Level Graders

You can also define graders per-task:

```yaml
# In task YAML
graders:
  - name: task_specific_check
    type: code
    assertions:
      - "specific_condition"
    weight: 0.5  # Weight within this task
```

---

## Grader Weights

When multiple graders are used, results are combined:

```yaml
graders:
  - type: code
    name: basic_check
    # Default weight: 1.0
  
  - type: llm
    name: quality_check
    # Default weight: 1.0
```

**Final Score:** Average of all grader scores (weighted if specified)

---

## Creating Custom Graders

Extend the `Grader` base class:

```python
from waza.graders.base import Grader, GraderContext, GraderType, GraderRegistry
from waza.schemas.results import GraderResult

@GraderRegistry.register("my_custom")
class MyCustomGrader(Grader):
    @property
    def grader_type(self) -> GraderType:
        return GraderType.CODE
    
    def grade(self, context: GraderContext) -> GraderResult:
        # Your logic here
        return GraderResult(
            name=self.name,
            type=self.grader_type.value,
            score=1.0,
            passed=True,
            message="Custom grading complete",
        )
```

Then use in eval.yaml:
```yaml
graders:
  - type: my_custom
    name: special_check
```
