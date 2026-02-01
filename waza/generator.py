"""Skill parser and eval generator.

Parses SKILL.md files and generates eval configurations automatically.
"""

from __future__ import annotations

import contextlib
import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
        self._escape_yaml_string(self.skill.description)[:60] if self.skill.description else ''

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
            "# Auto-generated from SKILL.md - customize as needed",
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
        # Note: We use explicit 'or' checks instead of generator expressions
        # because Python's eval() with restricted builtins doesn't allow
        # generator expressions to access outer scope variables
        keywords = self.skill.keywords[:3] if self.skill.keywords else []
        if keywords:
            # Build explicit 'or' chain: "'kw1' in output.lower() or 'kw2' in ..."
            checks = [f"'{kw.lower()}' in output.lower()" for kw in keywords]
            assertions = [" or ".join(checks)]
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
        """Generate sample fixture files dynamically based on SKILL.md content."""
        fixtures = []
        content_lower = self.skill.raw_content.lower()
        desc_lower = self.skill.description.lower() if self.skill.description else ""
        keywords_lower = ' '.join(self.skill.keywords).lower()
        all_text = f"{content_lower} {desc_lower} {keywords_lower}"

        # Detect file types mentioned in the skill
        file_patterns = {
            # Azure/Infrastructure
            'azure.yaml': 'azd' in all_text or 'azure developer cli' in all_text or 'azure.yaml' in all_text,
            'bicep': 'bicep' in all_text or 'infrastructure' in all_text or '.bicep' in all_text,
            'terraform': 'terraform' in all_text or '.tf' in all_text,
            # Containers
            'dockerfile': 'docker' in all_text or 'container' in all_text or 'dockerfile' in all_text,
            # Python
            'python': 'python' in all_text or '.py' in all_text or 'pip' in all_text,
            # JavaScript/TypeScript
            'javascript': 'javascript' in all_text or 'node' in all_text or '.js' in all_text,
            'typescript': 'typescript' in all_text or '.ts' in all_text,
            # Azure Functions
            'functions': 'function' in all_text and 'azure' in all_text,
            # Web/API
            'webapp': 'web app' in all_text or 'webapp' in all_text or 'fastapi' in all_text or 'flask' in all_text,
            # Config files
            'yaml_config': 'yaml' in all_text or 'yml' in all_text,
            'json_config': 'json' in all_text and ('config' in all_text or 'settings' in all_text),
        }

        # Generate fixtures based on detected patterns
        if file_patterns['azure.yaml']:
            fixtures.append(("azure.yaml", self._azure_yaml_template()))

        if file_patterns['bicep']:
            fixtures.append(("infra/main.bicep", self._bicep_template()))

        if file_patterns['terraform']:
            fixtures.append(("main.tf", self._terraform_template()))

        if file_patterns['dockerfile']:
            fixtures.append(("Dockerfile", self._dockerfile_template()))

        if file_patterns['functions']:
            fixtures.append(("function_app.py", self._azure_function_template()))
            fixtures.append(("host.json", self._host_json_template()))

        if file_patterns['python'] or file_patterns['webapp']:
            if not file_patterns['functions']:  # Don't duplicate if functions
                fixtures.append(("main.py", self._python_app_template()))
            fixtures.append(("requirements.txt", self._requirements_template()))

        if file_patterns['javascript']:
            fixtures.append(("index.js", self._js_template()))
            fixtures.append(("package.json", self._package_json_template()))

        if file_patterns['typescript']:
            fixtures.append(("src/index.ts", self._ts_template()))
            fixtures.append(("package.json", self._package_json_template(typescript=True)))
            fixtures.append(("tsconfig.json", self._tsconfig_template()))

        # Always include at least a README if nothing else matched
        if not fixtures:
            fixtures.append(("README.md", f"# Sample Project\\n\\nThis is a sample project for testing the {self.skill.name} skill.\\n"))
            fixtures.append(("main.py", self._python_app_template()))
            fixtures.append(("requirements.txt", "# Add your dependencies here\\n"))

        return fixtures

    # Template methods - simple, generic templates
    def _azure_yaml_template(self) -> str:
        return '''name: sample-app
metadata:
  template: sample@0.0.1
services:
  api:
    project: ./src
    language: python
    host: containerapp
'''

    def _bicep_template(self) -> str:
        return '''targetScope = 'subscription'

@description('Name of the environment')
param environmentName string

@description('Location for resources')
param location string = 'eastus'

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'rg-${environmentName}'
  location: location
}
'''

    def _terraform_template(self) -> str:
        return '''terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

variable "resource_group_name" {
  default = "rg-sample"
}

variable "location" {
  default = "eastus"
}
'''

    def _dockerfile_template(self) -> str:
        return '''FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
'''

    def _azure_function_template(self) -> str:
        return '''import azure.functions as func
import logging

app = func.FunctionApp()

@app.function_name(name="HttpTrigger")
@app.route(route="hello", auth_level=func.AuthLevel.ANONYMOUS)
def hello(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('HTTP trigger function processed a request.')
    name = req.params.get('name', 'World')
    return func.HttpResponse(f"Hello, {name}!")
'''

    def _host_json_template(self) -> str:
        return '''{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": { "isEnabled": true }
    }
  }
}
'''

    def _python_app_template(self) -> str:
        return '''from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/health")
def health():
    return {"status": "healthy"}
'''

    def _requirements_template(self) -> str:
        return '''fastapi
uvicorn
'''

    def _js_template(self) -> str:
        return '''const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.json({ message: 'Hello, World!' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
'''

    def _package_json_template(self, typescript: bool = False) -> str:
        if typescript:
            return '''{
  "name": "sample-app",
  "version": "1.0.0",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "ts-node src/index.ts"
  },
  "dependencies": {
    "express": "^4.18.2"
  },
  "devDependencies": {
    "@types/express": "^4.17.17",
    "@types/node": "^20.4.5",
    "typescript": "^5.1.6",
    "ts-node": "^10.9.1"
  }
}
'''
        return '''{
  "name": "sample-app",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "node index.js"
  },
  "dependencies": {
    "express": "^4.18.2"
  }
}
'''

    def _ts_template(self) -> str:
        return '''import express from 'express';

const app = express();

app.get('/', (req, res) => {
  res.json({ message: 'Hello, World!' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
'''

    def _tsconfig_template(self) -> str:
        return '''{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"]
}
'''

    def _safe_name(self, name: str) -> str:
        """Convert name to safe identifier."""
        return re.sub(r'[^a-zA-Z0-9-]', '-', name.lower()).strip('-')

    def _escape_yaml(self, s: str) -> str:
        """Escape string for YAML."""
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')


class AssistedGenerator:
    """LLM-assisted eval generation using Copilot SDK.

    Uses an LLM to analyze SKILL.md and generate more realistic,
    comprehensive test tasks, fixtures, and graders.
    """

    def __init__(
        self,
        skill: ParsedSkill,
        model: str = "claude-sonnet-4-20250514",
        console: Any = None,
    ):
        self.skill = skill
        self.model = model
        self.console = console
        self._client = None
        self._workspace = None

    async def setup(self) -> None:
        """Initialize Copilot client."""
        import tempfile
        try:
            from copilot import CopilotClient
        except ImportError as e:
            raise ImportError(
                "Copilot SDK not installed. Install with: pip install github-copilot-sdk\n"
                "Or run without --assist for pattern-based generation."
            ) from e

        self._workspace = tempfile.mkdtemp(prefix="skill-eval-assist-")
        self._client = CopilotClient({
            "cwd": self._workspace,
            "log_level": "error",
        })
        await self._client.start()

    async def teardown(self) -> None:
        """Clean up resources."""
        import shutil
        if self._client:
            await self._client.stop()
        if self._workspace:
            shutil.rmtree(self._workspace, ignore_errors=True)

    async def _call_llm(self, prompt: str) -> str:
        """Send prompt to LLM and get response."""
        import asyncio

        if not self._client:
            raise RuntimeError("Client not initialized. Call setup() first.")

        # Create a session
        session = await self._client.create_session({
            "model": self.model,
            "streaming": True,
        })

        output_parts: list[str] = []
        done_event = asyncio.Event()

        def handle_event(event) -> None:
            event_type = event.type.value if hasattr(event.type, 'value') else str(event.type)

            # Collect assistant messages
            if event_type == "assistant.message":
                if hasattr(event.data, 'content') and event.data.content:
                    output_parts.append(event.data.content)
            elif event_type == "assistant.message_delta" and hasattr(event.data, 'delta_content') and event.data.delta_content:
                output_parts.append(event.data.delta_content)

            # Check for completion
            if event_type == "session.idle" or event_type == "session.error":
                done_event.set()

        # Register event handler
        session.on(handle_event)

        # Send prompt
        await session.send({"prompt": prompt})

        # Wait for completion
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(done_event.wait(), timeout=120)

        # Cleanup
        with contextlib.suppress(Exception):
            await session.destroy()

        return "".join(output_parts)

    def _parse_json_response(self, response: str) -> Any:
        """Extract and parse JSON from LLM response."""
        import json

        # Try to find JSON in code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                response = response[start:end].strip()

        # Try to find JSON array or object
        for start_char, end_char in [('[', ']'), ('{', '}')]:
            start = response.find(start_char)
            if start >= 0:
                # Find matching end
                depth = 0
                for i, c in enumerate(response[start:], start):
                    if c == start_char:
                        depth += 1
                    elif c == end_char:
                        depth -= 1
                        if depth == 0:
                            try:
                                return json.loads(response[start:i+1])
                            except json.JSONDecodeError:
                                pass
                            break

        # Try parsing entire response
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return None

    async def generate_tasks(self) -> list[dict[str, Any]]:
        """Use LLM to generate realistic test tasks."""
        prompt = f"""Analyze this SKILL.md and generate 5 realistic test tasks for evaluating this skill.

SKILL.md Content:
---
{self.skill.raw_content[:4000]}
---

Skill Name: {self.skill.name}
Description: {self.skill.description}
Triggers: {', '.join(self.skill.triggers[:5])}

Generate 5 diverse test tasks that:
1. Use natural language prompts (as a real user would ask)
2. Test different capabilities of the skill
3. Range from simple to complex scenarios
4. Include edge cases

Return ONLY a JSON array with this structure:
[
  {{
    "id": "task-001",
    "name": "Short descriptive name",
    "prompt": "The user's natural language request",
    "description": "What this task tests",
    "expected_keywords": ["keyword1", "keyword2"],
    "difficulty": "easy|medium|hard"
  }}
]

Return ONLY the JSON array, no explanation."""

        response = await self._call_llm(prompt)
        tasks = self._parse_json_response(response)

        if not tasks or not isinstance(tasks, list):
            return []

        # Validate and clean tasks
        valid_tasks = []
        for i, task in enumerate(tasks[:5]):
            if isinstance(task, dict) and "prompt" in task:
                valid_tasks.append({
                    "id": task.get("id", f"{self._safe_name()}-{i+1:03d}"),
                    "name": task.get("name", f"Task {i+1}"),
                    "prompt": task.get("prompt", ""),
                    "description": task.get("description", ""),
                    "expected_keywords": task.get("expected_keywords", []),
                    "difficulty": task.get("difficulty", "medium"),
                })

        return valid_tasks

    async def generate_fixtures(self) -> list[tuple[str, str]]:
        """Use LLM to generate appropriate fixture files."""
        prompt = f"""Based on this skill, generate realistic project files that a user would have when using this skill.

Skill: {self.skill.name}
Description: {self.skill.description}
Triggers: {', '.join(self.skill.triggers[:5])}

Content preview:
{self.skill.raw_content[:2000]}

Generate 3-5 realistic project files that would be in a user's workspace.
Files should be appropriate for the skill's domain (e.g., Azure config files, code files, etc.)

Return ONLY a JSON array with this structure:
[
  {{
    "filename": "path/to/file.ext",
    "content": "file content here",
    "purpose": "why this file is relevant"
  }}
]

Keep files realistic but concise (under 50 lines each).
Return ONLY the JSON array, no explanation."""

        response = await self._call_llm(prompt)
        files = self._parse_json_response(response)

        if not files or not isinstance(files, list):
            return []

        fixtures = []
        for f in files[:5]:
            if isinstance(f, dict) and "filename" in f and "content" in f:
                fixtures.append((f["filename"], f["content"]))

        return fixtures

    async def suggest_graders(self, tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Use LLM to suggest appropriate graders for tasks."""
        task_summary = "\n".join([
            f"- {t.get('name', 'Task')}: {t.get('prompt', '')[:100]}"
            for t in tasks[:5]
        ])

        prompt = f"""For these test tasks, suggest appropriate graders/assertions to validate the skill's behavior.

Skill: {self.skill.name}
Tasks:
{task_summary}

IMPORTANT CONTEXT about available variables:
- `output` = the final assistant text response (usually a summary/explanation, NOT code)
- `transcript` = list of all conversation turns including tool calls
- `tool_calls` = list of tool calls made (each has 'tool_name' and 'arguments')

For skills that EDIT CODE, the code changes are in tool_calls, NOT in output.
To check if code was written, use: "any('edit' in str(t) for t in tool_calls)" or check transcript.

Suggest graders that check:
1. Output contains relevant explanation/summary
2. No dangerous commands were executed
3. Appropriate tools were used
4. Response addresses the user's request

Return ONLY a JSON array with grader configs:
[
  {{
    "name": "grader_name",
    "type": "code",
    "assertions": ["python expression that evaluates to True if passed"],
    "description": "what this grader checks"
  }}
]

IMPORTANT: Only use "type": "code" - assertions must be valid Python expressions.
Examples of good assertions:
- "len(output) > 0"
- "'azure' in output.lower() or 'container' in output.lower()"
- "len(tool_calls) > 0"
- "'rm -rf' not in str(transcript)"

DO NOT use generator expressions like any(x for x in ...) - they won't work in eval context.
Use explicit 'or' chains instead: "'a' in output or 'b' in output"

Focus on 2-3 simple graders. Keep assertions simple and likely to pass if the skill works.
Return ONLY the JSON array, no explanation."""

        response = await self._call_llm(prompt)
        graders = self._parse_json_response(response)

        if not graders or not isinstance(graders, list):
            return self._default_graders()

        # Filter to only supported grader types and ensure valid structure
        valid_graders = []
        for g in graders[:5]:
            if isinstance(g, dict) and "name" in g:
                # Force type to "code" if invalid
                g_type = g.get("type", "code")
                if g_type not in ("code", "regex", "llm"):
                    g_type = "code"
                valid_graders.append({
                    "name": g.get("name", "check"),
                    "type": g_type,
                    "assertions": g.get("assertions", []),
                    "description": g.get("description", ""),
                })

        return valid_graders if valid_graders else self._default_graders()

    def _default_graders(self) -> list[dict[str, Any]]:
        """Return default graders if LLM fails."""
        return [
            {
                "name": "output_check",
                "type": "code",
                "assertions": ["len(output) > 0"],
                "description": "Basic output validation",
            },
            {
                "name": "no_dangerous_commands",
                "type": "code",
                "assertions": [
                    "'rm -rf /' not in output",
                    "'drop database' not in output.lower()",
                ],
                "description": "Safety check",
            },
        ]

    def _safe_name(self) -> str:
        """Convert skill name to safe identifier."""
        return re.sub(r'[^a-zA-Z0-9-]', '-', self.skill.name.lower()).strip('-')

    def format_task_yaml(self, task: dict[str, Any], graders: list[dict[str, Any]]) -> str:
        """Format a task dict as YAML."""
        # Escape prompt (don't truncate - full prompt is needed!)
        prompt = task.get("prompt", "").replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')

        keywords = task.get("expected_keywords", [])[:5]
        keywords_yaml = "\n".join(f'    - "{k}"' for k in keywords) if keywords else f'    - "{self.skill.name.lower()}"'

        graders_yaml = ""
        for g in graders[:3]:
            graders_yaml += f"""
  - name: {g.get('name', 'check')}
    type: {g.get('type', 'code')}
    assertions:"""
            for a in g.get("assertions", ["len(output) > 0"])[:3]:
                # Escape backslashes and quotes in assertions
                a_escaped = str(a).replace('\\', '\\\\').replace('"', '\\"')
                graders_yaml += f'\n      - "{a_escaped}"'

        return f"""---
# {task.get('name', 'Task')}
# LLM-generated task - review and customize
id: {task.get('id', 'task-001')}
name: "{task.get('name', 'Task')}"
description: "{task.get('description', '')[:60]}"

inputs:
  prompt: "{prompt}"
  context: {{}}

expected:
  outcomes:
    - type: task_completed
  output_contains:
{keywords_yaml}

  behavior:
    max_tool_calls: 20
    max_iterations: 10

graders:{graders_yaml}
"""

    async def generate_all(self) -> dict[str, Any]:
        """Generate all eval components using LLM assistance.

        Returns:
            Dict with 'tasks', 'fixtures', 'graders' keys
        """
        if self.console:
            from rich.progress import Progress, SpinnerColumn, TextColumn

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task1 = progress.add_task("[cyan]Generating tasks...", total=None)
                tasks = await self.generate_tasks()
                progress.update(task1, description=f"[green]✓ Generated {len(tasks)} tasks")

                task2 = progress.add_task("[cyan]Generating fixtures...", total=None)
                fixtures = await self.generate_fixtures()
                progress.update(task2, description=f"[green]✓ Generated {len(fixtures)} fixtures")

                task3 = progress.add_task("[cyan]Suggesting graders...", total=None)
                graders = await self.suggest_graders(tasks)
                progress.update(task3, description=f"[green]✓ Suggested {len(graders)} graders")
        else:
            tasks = await self.generate_tasks()
            fixtures = await self.generate_fixtures()
            graders = await self.suggest_graders(tasks)

        return {
            "tasks": tasks,
            "fixtures": fixtures,
            "graders": graders,
        }
