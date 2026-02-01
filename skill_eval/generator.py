"""Skill parser and eval generator.

Parses SKILL.md files and generates eval configurations automatically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import urllib.request
import yaml


@dataclass
class ParsedSkill:
    """Parsed skill information from SKILL.md."""
    
    name: str
    description: str
    triggers: list[str] = field(default_factory=list)
    anti_triggers: list[str] = field(default_factory=list)
    cli_commands: list[str] = field(default_factory=list)
    mcp_tools: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    best_practices: list[str] = field(default_factory=list)
    examples: list[dict[str, str]] = field(default_factory=list)
    raw_content: str = ""


class SkillParser:
    """Parse SKILL.md files to extract structured information."""
    
    def parse(self, content: str) -> ParsedSkill:
        """Parse SKILL.md content into structured data."""
        skill = ParsedSkill(
            name="",
            description="",
            raw_content=content,
        )
        
        # Extract frontmatter if present
        frontmatter = self._extract_frontmatter(content)
        if frontmatter:
            skill.name = frontmatter.get("name", "")
            skill.description = frontmatter.get("description", "")
        
        # Extract name from first heading if not in frontmatter
        if not skill.name:
            skill.name = self._extract_first_heading(content)
        
        # Extract trigger phrases
        skill.triggers = self._extract_triggers(content)
        skill.anti_triggers = self._extract_anti_triggers(content)
        
        # Extract CLI commands
        skill.cli_commands = self._extract_cli_commands(content)
        
        # Extract MCP tools
        skill.mcp_tools = self._extract_mcp_tools(content)
        
        # Extract keywords from description and content
        skill.keywords = self._extract_keywords(content, skill.description)
        
        # Extract best practices
        skill.best_practices = self._extract_best_practices(content)
        
        # Extract examples/use cases
        skill.examples = self._extract_examples(content)
        
        return skill
    
    def parse_file(self, path: str | Path) -> ParsedSkill:
        """Parse a SKILL.md file."""
        path = Path(path)
        content = path.read_text()
        skill = self.parse(content)
        if not skill.name:
            skill.name = path.parent.name
        return skill
    
    def parse_url(self, url: str) -> ParsedSkill:
        """Parse a SKILL.md from a URL (GitHub raw or regular)."""
        # Convert GitHub blob URL to raw URL
        if "github.com" in url and "/blob/" in url:
            url = url.replace("github.com", "raw.githubusercontent.com")
            url = url.replace("/blob/", "/")
        
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")
        
        skill = self.parse(content)
        
        # Extract name from URL path if not found
        if not skill.name:
            parts = url.rstrip("/").split("/")
            # Try to find skill name from path (usually parent of SKILL.md)
            if "SKILL.md" in parts[-1].upper():
                skill.name = parts[-2] if len(parts) > 1 else "unknown"
        
        return skill
    
    def _extract_frontmatter(self, content: str) -> dict[str, Any]:
        """Extract YAML frontmatter from content."""
        match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                return {}
        return {}
    
    def _extract_first_heading(self, content: str) -> str:
        """Extract first H1 heading."""
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else ""
    
    def _extract_triggers(self, content: str) -> list[str]:
        """Extract trigger phrases from skill activation section."""
        triggers = []
        
        # Look for "Skill Activation Triggers" or similar sections
        trigger_section = re.search(
            r'(?:Skill Activation|Use this skill|Trigger|When to use).*?(?=\n##|\n\*\*Key|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        if trigger_section:
            section = trigger_section.group(0)
            # Extract quoted phrases
            triggers.extend(re.findall(r'"([^"]+)"', section))
            # Extract list items that look like prompts
            triggers.extend(re.findall(r'[-*]\s*["\']?([^"\'\n]+(?:deploy|create|set up|configure|help)[^"\'\n]*)["\']?', section, re.IGNORECASE))
        
        # Also look for USE FOR patterns in description
        use_for = re.search(r'USE FOR[:\s]+([^.]+)', content, re.IGNORECASE)
        if use_for:
            triggers.extend([t.strip() for t in use_for.group(1).split(',')])
        
        # Deduplicate and clean
        seen = set()
        clean_triggers = []
        for t in triggers:
            t = t.strip().rstrip('.,;')
            if t and t.lower() not in seen and len(t) > 5:
                seen.add(t.lower())
                clean_triggers.append(t)
        
        return clean_triggers[:15]  # Limit to reasonable number
    
    def _extract_anti_triggers(self, content: str) -> list[str]:
        """Extract phrases that should NOT trigger this skill."""
        anti_triggers = []
        
        # Look for "DO NOT USE FOR" or similar
        dont_use = re.search(r'(?:DO NOT USE|Don\'t use|Not for)[:\s]+([^.]+)', content, re.IGNORECASE)
        if dont_use:
            anti_triggers.extend([t.strip() for t in dont_use.group(1).split(',')])
        
        # Look for explicit "should not trigger" sections
        not_section = re.search(
            r'(?:should not|shouldn\'t|don\'t).*?trigger.*?(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        if not_section:
            anti_triggers.extend(re.findall(r'"([^"]+)"', not_section.group(0)))
        
        return [t.strip() for t in anti_triggers if t.strip()][:10]
    
    def _extract_cli_commands(self, content: str) -> list[str]:
        """Extract CLI command patterns from code blocks."""
        commands = set()
        
        # Find bash/shell code blocks
        code_blocks = re.findall(r'```(?:bash|shell|sh)?\s*\n(.*?)```', content, re.DOTALL)
        
        for block in code_blocks:
            # Extract command prefixes (first word of lines starting with common patterns)
            for line in block.split('\n'):
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                # Get the main command
                match = re.match(r'^(az|func|azd|kubectl|docker|npm|pip|dotnet|git)\s+\S+', line)
                if match:
                    commands.add(match.group(0).split()[0])
                # Also capture subcommands
                match = re.match(r'^(az\s+\w+|func\s+\w+|azd\s+\w+)', line)
                if match:
                    commands.add(match.group(1))
        
        return sorted(commands)
    
    def _extract_mcp_tools(self, content: str) -> list[str]:
        """Extract MCP tool references."""
        tools = set()
        
        # Look for azure__ prefixed tools
        tools.update(re.findall(r'azure__\w+', content))
        
        # Look for tool table references
        tool_matches = re.findall(r'`(azure[_-]\w+)`', content)
        tools.update(tool_matches)
        
        return sorted(tools)
    
    def _extract_keywords(self, content: str, description: str) -> list[str]:
        """Extract important keywords for grading."""
        keywords = set()
        priority_keywords = set()  # Keywords directly from skill name/description
        
        # Add key terms from skill name
        skill_name_words = re.findall(r'[a-zA-Z]+', self.name.lower() if hasattr(self, 'name') else '')
        priority_keywords.update(w for w in skill_name_words if len(w) > 3)
        
        # Add key terms from description (high priority)
        if description:
            # Look for capitalized terms (likely proper nouns/product names)
            words = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', description)
            priority_keywords.update(w.lower() for w in words if len(w) > 3)
            # Also lowercase important terms
            words = re.findall(r'\b([a-z]{4,})\b', description.lower())
            priority_keywords.update(words)
        
        # Extract from headers (good signal for topic keywords)
        headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        for h in headers:
            # Only alphanumeric words
            words = re.findall(r'\b([a-zA-Z]{4,})\b', h)
            keywords.update(w.lower() for w in words)
        
        # Extract technical terms (CamelCase patterns)
        tech_terms = re.findall(r'\b([A-Z][a-z]+[A-Z]\w+)\b', content)
        keywords.update(t.lower() for t in tech_terms)
        
        # Common filter words to remove
        stop_words = {
            'the', 'and', 'for', 'with', 'this', 'that', 'from', 'your', 
            'when', 'what', 'how', 'about', 'into', 'which', 'will', 'should',
            'would', 'could', 'have', 'been', 'being', 'here', 'there', 'where',
            'example', 'examples', 'section', 'overview', 'introduction', 'note',
            'important', 'warning', 'skill', 'skills', 'using', 'used', 'uses',
            'access', 'account', 'actions', 'additional', 'activation'
        }
        
        # Filter: alphanumeric only, not stop words, reasonable length
        priority_keywords = {
            k for k in priority_keywords 
            if k not in stop_words and len(k) >= 4 and k.isalpha()
        }
        keywords = {
            k for k in keywords 
            if k not in stop_words and len(k) >= 4 and k.isalpha()
        }
        
        # Priority keywords first, then general keywords
        result = sorted(priority_keywords) + sorted(keywords - priority_keywords)
        return result[:20]
    
    def _extract_best_practices(self, content: str) -> list[str]:
        """Extract best practices mentioned in the skill."""
        practices = []
        
        # Look for best practices section
        bp_section = re.search(
            r'(?:Best Practices|Recommendations|Guidelines).*?(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        if bp_section:
            # Extract table rows or list items
            practices.extend(re.findall(r'\|\s*\*\*([^|*]+)\*\*\s*\|', bp_section.group(0)))
            practices.extend(re.findall(r'[-*]\s+\*\*([^*]+)\*\*', bp_section.group(0)))
        
        return [p.strip() for p in practices if p.strip()][:10]
    
    def _extract_examples(self, content: str) -> list[dict[str, str]]:
        """Extract example use cases."""
        examples = []
        
        # Look for example prompts in quotes
        prompts = re.findall(r'"([^"]{20,})"', content)
        for p in prompts[:5]:
            if any(word in p.lower() for word in ['create', 'deploy', 'set up', 'configure', 'help', 'how']):
                examples.append({"prompt": p, "type": "user_request"})
        
        return examples


class EvalGenerator:
    """Generate eval configurations from parsed skills."""
    
    def __init__(self, skill: ParsedSkill):
        self.skill = skill
    
    def _escape_yaml_string(self, s: str) -> str:
        """Escape a string for safe YAML output."""
        if not s:
            return ""
        # Remove any characters that could break YAML
        # Keep only the first sentence/line and sanitize
        s = s.split('\n')[0]  # First line only
        s = re.sub(r'[:\|>\[\]{}#&*!?,]', '', s)  # Remove YAML special chars
        s = s[:200]  # Limit length
        return s.strip()
    
    def generate_eval_yaml(self) -> str:
        """Generate eval.yaml content."""
        # Build graders based on extracted info
        graders = self._generate_graders()
        
        # Safely escape description - limit to 60 chars for line length
        desc = self._escape_yaml_string(self.skill.description)[:60] if self.skill.description else ''
        
        yaml_content = f"""---
# Auto-generated eval specification for {self.skill.name}
# Generated from SKILL.md - customize as needed
name: {self._safe_name(self.skill.name)}-eval
description: Evaluation suite for the {self.skill.name} skill.
skill: {self._safe_name(self.skill.name)}
version: "1.0"

config:
  trials_per_task: 1
  timeout_seconds: 300
  parallel: false
  executor: mock  # Use 'copilot-sdk' for real integration tests

metrics:
  - name: task_completion
    weight: 0.4
    threshold: 0.8
    description: Did the skill accomplish the requested task?

  - name: trigger_accuracy
    weight: 0.3
    threshold: 0.9
    description: Is the skill invoked on the right prompts?

  - name: behavior_quality
    weight: 0.3
    threshold: 0.7
    description: Tool usage and best practices adherence

graders:
{self._format_graders(graders)}

tasks:
  - "tasks/*.yaml"
"""
        return yaml_content
    
    def generate_trigger_tests(self) -> str:
        """Generate trigger_tests.yaml content."""
        should_trigger = []
        should_not_trigger = []
        
        # Use extracted triggers
        for i, trigger in enumerate(self.skill.triggers[:10]):
            should_trigger.append({
                "prompt": trigger,
                "reason": f"Skill activation phrase #{i+1}"
            })
        
        # Add generic triggers based on skill name
        skill_words = self.skill.name.lower().replace('-', ' ').split()
        should_trigger.append({
            "prompt": f"Help me with {' '.join(skill_words)}",
            "reason": "Generic skill request"
        })
        
        # Use extracted anti-triggers
        for anti in self.skill.anti_triggers[:5]:
            should_not_trigger.append({
                "prompt": anti,
                "reason": "Explicitly excluded use case"
            })
        
        # Add generic anti-triggers
        should_not_trigger.extend([
            {"prompt": "What is the weather today?", "reason": "Unrelated question"},
            {"prompt": "Tell me a joke", "reason": "Entertainment request"},
            {"prompt": "What time is it?", "reason": "General question"},
        ])
        
        lines = [
            "---",
            f"# Trigger accuracy tests for {self.skill.name}",
            f"# Auto-generated from SKILL.md - customize as needed",
            f"skill: {self._safe_name(self.skill.name)}",
            "",
            "should_trigger_prompts:",
        ]
        
        for item in should_trigger:
            # Truncate long prompts for line length
            prompt = self._escape_yaml(item["prompt"])[:60]
            lines.append(f'  - prompt: "{prompt}"')
            lines.append(f'    reason: "{item["reason"]}"')
            lines.append("")
        
        lines.append("should_not_trigger_prompts:")
        for item in should_not_trigger:
            prompt = self._escape_yaml(item["prompt"])[:60]
            lines.append(f'  - prompt: "{prompt}"')
            lines.append(f'    reason: "{item["reason"]}"')
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_task(self, prompt: str, task_id: str, task_name: str) -> str:
        """Generate a task YAML for a specific prompt."""
        # Determine expected patterns based on skill
        expected_keywords = self.skill.keywords[:5] if self.skill.keywords else [self.skill.name.lower()]
        cli_patterns = self.skill.cli_commands[:3] if self.skill.cli_commands else []
        
        # Truncate prompt for line length
        escaped_prompt = self._escape_yaml(prompt)[:60]
        
        yaml_content = f"""---
# {task_name}
# Auto-generated task - customize as needed
id: {task_id}
name: {task_name}
description: Test task for {self.skill.name} skill

inputs:
  prompt: "{escaped_prompt}"
  context: {{}}

expected:
  outcomes:
    - type: task_completed

  output_contains:
{self._format_list(expected_keywords, indent=4)}

"""
        
        if cli_patterns:
            yaml_content += f"""  tool_calls:
    required:
{self._format_patterns(cli_patterns, indent=6)}
    forbidden:
      - pattern: "rm -rf"
      - pattern: "delete.*subscription"

"""
        
        yaml_content += """  behavior:
    max_tool_calls: 20
    max_iterations: 10

graders:
  - name: output_check
    type: code
    assertions:
      - "len(output) > 0"
"""
        
        return yaml_content
    
    def generate_example_tasks(self) -> list[tuple[str, str]]:
        """Generate example task files based on skill examples."""
        tasks = []
        
        # Generate from extracted examples
        for i, example in enumerate(self.skill.examples[:3]):
            task_id = f"{self._safe_name(self.skill.name)}-{i+1:03d}"
            task_name = f"Example Task {i+1}"
            content = self.generate_task(example["prompt"], task_id, task_name)
            filename = f"task-{i+1:03d}.yaml"
            tasks.append((filename, content))
        
        # Generate from triggers if no examples
        if not tasks and self.skill.triggers:
            for i, trigger in enumerate(self.skill.triggers[:3]):
                task_id = f"{self._safe_name(self.skill.name)}-{i+1:03d}"
                task_name = f"Trigger Task {i+1}"
                content = self.generate_task(trigger, task_id, task_name)
                filename = f"task-{i+1:03d}.yaml"
                tasks.append((filename, content))
        
        # Always generate at least one example task
        if not tasks:
            task_id = f"{self._safe_name(self.skill.name)}-001"
            prompt = f"Help me use {self.skill.name}"
            content = self.generate_task(prompt, task_id, "Example Task")
            tasks.append(("example-task.yaml", content))
        
        return tasks
    
    def _generate_graders(self) -> list[dict[str, Any]]:
        """Generate grader configurations based on skill info."""
        graders = []
        
        # Output validation grader
        keywords = self.skill.keywords[:3] if self.skill.keywords else []
        if keywords:
            assertions = [f"any(kw in output.lower() for kw in {keywords})"]
        else:
            assertions = ["len(output) > 0"]
        
        graders.append({
            "type": "code",
            "name": "output_validation",
            "config": {"assertions": assertions}
        })
        
        # CLI command grader if we have commands
        if self.skill.cli_commands:
            cmd_pattern = "|".join(self.skill.cli_commands[:5])
            graders.append({
                "type": "regex",
                "name": "cli_commands_used",
                "config": {
                    "pattern": cmd_pattern,
                    "should_match": True
                }
            })
        
        # Safety grader
        graders.append({
            "type": "regex",
            "name": "no_dangerous_commands",
            "config": {
                "pattern": r"rm\s+-rf|delete.*subscription|DROP\s+DATABASE",
                "should_match": False
            }
        })
        
        return graders
    
    def _format_graders(self, graders: list[dict]) -> str:
        """Format graders for YAML output."""
        lines = []
        for g in graders:
            lines.append(f"  - type: {g['type']}")
            lines.append(f"    name: {g['name']}")
            if 'config' in g:
                lines.append("    config:")
                for key, value in g['config'].items():
                    if isinstance(value, list):
                        lines.append(f"      {key}:")
                        for item in value:
                            lines.append(f'        - "{self._escape_yaml(str(item))}"')
                    elif isinstance(value, bool):
                        lines.append(f"      {key}: {'true' if value else 'false'}")
                    else:
                        lines.append(f'      {key}: "{self._escape_yaml(str(value))}"')
            lines.append("")
        return "\n".join(lines)
    
    def _format_list(self, items: list[str], indent: int = 2) -> str:
        """Format a list for YAML."""
        prefix = " " * indent
        return "\n".join(f'{prefix}- "{self._escape_yaml(item)}"' for item in items)
    
    def _format_patterns(self, patterns: list[str], indent: int = 2) -> str:
        """Format patterns for tool_calls section."""
        prefix = " " * indent
        return "\n".join(f'{prefix}- pattern: "{self._escape_yaml(p)}"' for p in patterns)
    
    def generate_fixtures(self) -> list[tuple[str, str]]:
        """Generate sample fixture files based on skill type."""
        fixtures = []
        skill_lower = self.skill.name.lower()
        
        # Azure Functions fixtures
        if 'function' in skill_lower or 'azure-functions' in skill_lower:
            fixtures.extend(self._generate_azure_function_fixtures())
        
        # Deploy/Container fixtures
        elif 'deploy' in skill_lower or 'container' in skill_lower:
            fixtures.extend(self._generate_deploy_fixtures())
        
        # Code/Explainer fixtures
        elif 'code' in skill_lower or 'explain' in skill_lower:
            fixtures.extend(self._generate_code_fixtures())
        
        # Generic Python fixtures
        elif 'python' in skill_lower:
            fixtures.extend(self._generate_python_fixtures())
        
        # Generic JavaScript/TypeScript fixtures  
        elif 'javascript' in skill_lower or 'typescript' in skill_lower or 'node' in skill_lower:
            fixtures.extend(self._generate_js_fixtures())
        
        # Default: minimal generic fixtures
        if not fixtures:
            fixtures.extend(self._generate_generic_fixtures())
        
        return fixtures
    
    def _generate_azure_function_fixtures(self) -> list[tuple[str, str]]:
        """Generate Azure Functions sample files."""
        return [
            ("function_app.py", '''import azure.functions as func
import logging

app = func.FunctionApp()

@app.function_name(name="HttpTrigger")
@app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
def hello_http(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')
    
    if name:
        return func.HttpResponse(f"Hello, {name}!")
    else:
        return func.HttpResponse(
            "Please pass a name on the query string or in the request body",
            status_code=400
        )
'''),
            ("host.json", '''{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
'''),
            ("requirements.txt", '''azure-functions
'''),
            ("local.settings.json", '''{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python"
  }
}
'''),
        ]
    
    def _generate_deploy_fixtures(self) -> list[tuple[str, str]]:
        """Generate deployment sample files."""
        return [
            ("Dockerfile", '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''),
            ("main.py", '''from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
'''),
            ("requirements.txt", '''fastapi
uvicorn
'''),
        ]
    
    def _generate_code_fixtures(self) -> list[tuple[str, str]]:
        """Generate code sample files for code explainer skills."""
        return [
            ("sample_python.py", '''def fibonacci(n: int) -> list[int]:
    """Generate Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence


def binary_search(arr: list[int], target: int) -> int:
    """Binary search for target in sorted array. Returns index or -1."""
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1
'''),
            ("sample_javascript.js", '''// Async function to fetch data with retry
async function fetchWithRetry(url, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      if (attempt === maxRetries) throw error;
      await new Promise(r => setTimeout(r, 1000 * attempt));
    }
  }
}

// Debounce utility function
function debounce(fn, delay) {
  let timeoutId;
  return function(...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(this, args), delay);
  };
}
'''),
        ]
    
    def _generate_python_fixtures(self) -> list[tuple[str, str]]:
        """Generate Python project fixtures."""
        return [
            ("main.py", '''"""Main application entry point."""
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Application starting...")
    # Your application logic here
    logger.info("Application finished.")


if __name__ == "__main__":
    main()
'''),
            ("requirements.txt", '''# Add your dependencies here
'''),
        ]
    
    def _generate_js_fixtures(self) -> list[tuple[str, str]]:
        """Generate JavaScript/Node.js project fixtures."""
        return [
            ("index.js", '''const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
  res.json({ message: 'Hello, World!' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
'''),
            ("package.json", '''{
  "name": "sample-app",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "node --watch index.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
'''),
        ]
    
    def _generate_generic_fixtures(self) -> list[tuple[str, str]]:
        """Generate minimal generic fixtures."""
        return [
            ("README.md", f'''# Sample Project

This is a sample project for testing the {self.skill.name} skill.

## Getting Started

Add your project files here to provide context for the skill evaluation.
'''),
        ]
    
    def _safe_name(self, name: str) -> str:
        """Convert name to safe identifier."""
        return re.sub(r'[^a-zA-Z0-9-]', '-', name.lower()).strip('-')
    
    def _escape_yaml(self, s: str) -> str:
        """Escape string for YAML."""
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
