"""CLI entrypoint for skill-eval."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from skill_eval import __version__
from skill_eval.schemas.eval_spec import EvalSpec
from skill_eval.schemas.task import Task
from skill_eval.runner import EvalRunner
from skill_eval.reporters import JSONReporter, MarkdownReporter, GitHubReporter

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="skill-eval")
def main():
    """Skill Eval - Evaluate Agent Skills like you evaluate AI Agents."""
    pass


@main.command()
@click.argument("eval_path", type=click.Path(exists=True))
@click.option("--task", "-t", multiple=True, help="Run specific task(s) by ID")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "-f", type=click.Choice(["json", "markdown", "github"]), default="json", help="Output format")
@click.option("--trials", type=int, help="Override trials per task")
@click.option("--parallel/--no-parallel", default=None, help="Run tasks in parallel")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--fail-threshold", type=float, default=0.0, help="Fail if pass rate below threshold")
@click.option("--model", "-m", type=str, help="Model to use for execution (e.g., claude-sonnet-4-20250514, gpt-4)")
@click.option("--executor", "-e", type=click.Choice(["mock", "copilot-sdk"]), help="Executor type")
def run(
    eval_path: str,
    task: tuple[str, ...],
    output: Optional[str],
    format: str,
    trials: Optional[int],
    parallel: Optional[bool],
    verbose: bool,
    fail_threshold: float,
    model: Optional[str],
    executor: Optional[str],
):
    """Run an evaluation suite.
    
    EVAL_PATH: Path to the eval.yaml file
    """
    console.print(f"[bold blue]skill-eval[/bold blue] v{__version__}")
    console.print()

    # Load spec
    try:
        spec = EvalSpec.from_file(eval_path)
        console.print(f"[green]✓[/green] Loaded eval: [bold]{spec.name}[/bold]")
        console.print(f"  Skill: {spec.skill}")
    except Exception as e:
        console.print(f"[red]✗ Failed to load eval spec:[/red] {e}")
        sys.exit(1)

    # Apply overrides
    if trials:
        spec.config.trials_per_task = trials
    if parallel is not None:
        spec.config.parallel = parallel
    if model:
        spec.config.model = model
    if executor:
        from skill_eval.schemas.eval_spec import ExecutorType
        spec.config.executor = ExecutorType(executor)
    spec.config.verbose = verbose

    # Display executor/model info
    console.print(f"  Executor: {spec.config.executor.value}")
    console.print(f"  Model: {spec.config.model}")

    # Create base path for task loading
    base_path = Path(eval_path).parent

    # Load and filter tasks (using temporary runner just for loading)
    try:
        temp_runner = EvalRunner(spec=spec, base_path=base_path)
        tasks = temp_runner.load_tasks()
        if task:
            tasks = [t for t in tasks if t.id in task]
        
        if not tasks:
            console.print("[yellow]⚠ No tasks to run[/yellow]")
            sys.exit(0)
        
        console.print(f"  Tasks: {len(tasks)}")
        console.print(f"  Trials per task: {spec.config.trials_per_task}")
        console.print()
    except Exception as e:
        console.print(f"[red]✗ Failed to load tasks:[/red] {e}")
        sys.exit(1)

    # Create progress display
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.table import Table
    
    # Track progress state
    progress_state = {
        "current_task": "",
        "current_task_num": 0,
        "total_tasks": len(tasks),
        "current_trial": 0,
        "total_trials": spec.config.trials_per_task,
        "completed_tasks": [],
        "status": "running",
    }
    
    def make_progress_table() -> Table:
        """Create the progress display table."""
        table = Table.grid(padding=(0, 1))
        table.add_column(justify="right", width=12)
        table.add_column()
        
        # Progress bar
        completed = len(progress_state["completed_tasks"])
        total = progress_state["total_tasks"]
        pct = (completed / total * 100) if total > 0 else 0
        bar_width = 30
        filled = int(bar_width * completed / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        
        table.add_row(
            "[bold]Progress:[/bold]",
            f"[green]{bar}[/green] {completed}/{total} ({pct:.0f}%)"
        )
        
        if progress_state["current_task"]:
            task_name = progress_state["current_task"][:40]
            trial_info = ""
            if progress_state["total_trials"] > 1:
                trial_info = f" (trial {progress_state['current_trial']}/{progress_state['total_trials']})"
            table.add_row(
                "[bold]Running:[/bold]",
                f"[cyan]{task_name}[/cyan]{trial_info}"
            )
        
        # Show last completed task in verbose mode
        if verbose and progress_state["completed_tasks"]:
            last = progress_state["completed_tasks"][-1]
            icon = "✅" if last["status"] == "passed" else "❌"
            table.add_row(
                "[bold]Last:[/bold]",
                f"{icon} {last['name'][:35]} ({last['duration_ms']}ms)"
            )
        
        return table
    
    def progress_callback(
        event: str,
        task_name: str | None = None,
        task_num: int | None = None,
        total_tasks: int | None = None,
        trial_num: int | None = None,
        total_trials: int | None = None,
        status: str | None = None,
        duration_ms: int | None = None,
        details: dict | None = None,
    ):
        """Handle progress updates from the runner."""
        if event == "task_start":
            progress_state["current_task"] = task_name or ""
            progress_state["current_task_num"] = task_num or 0
            progress_state["current_trial"] = 1
        elif event == "trial_start":
            progress_state["current_trial"] = trial_num or 1
            progress_state["total_trials"] = total_trials or 1
        elif event == "task_complete":
            progress_state["completed_tasks"].append({
                "name": task_name,
                "status": status,
                "duration_ms": duration_ms or 0,
                "score": details.get("score", 0) if details else 0,
            })
            progress_state["current_task"] = ""
    
    # Create runner with progress callback
    runner = EvalRunner(spec=spec, base_path=base_path, progress_callback=progress_callback)

    # Run with live progress display
    with Live(make_progress_table(), console=console, refresh_per_second=4) as live:
        import asyncio
        
        async def run_with_progress():
            while True:
                live.update(make_progress_table())
                await asyncio.sleep(0.25)
        
        async def run_eval():
            return await runner.run_async(tasks)
        
        async def main_loop():
            eval_task = asyncio.create_task(run_eval())
            
            # Update display while eval runs
            while not eval_task.done():
                live.update(make_progress_table())
                await asyncio.sleep(0.1)
            
            return await eval_task
        
        result = asyncio.run(main_loop())

    # Display results
    _display_results(result, verbose)

    # Output to file
    if output:
        if format == "json":
            reporter = JSONReporter()
            reporter.report_to_file(result, output)
        elif format == "markdown":
            reporter = MarkdownReporter()
            reporter.report_to_file(result, output)
        elif format == "github":
            reporter = GitHubReporter()
            Path(output).write_text(reporter.report_summary(result))
        
        console.print(f"\n[green]✓[/green] Results written to: {output}")

    # Check threshold
    if result.summary.pass_rate < fail_threshold:
        console.print(f"\n[red]✗ Pass rate {result.summary.pass_rate:.1%} below threshold {fail_threshold:.1%}[/red]")
        sys.exit(1)


@main.command()
@click.argument("skill_name")
@click.option("--path", "-p", type=click.Path(), default=".", help="Output directory")
@click.option("--from-skill", "-s", type=str, help="Path or URL to SKILL.md to generate from")
def init(skill_name: str, path: str, from_skill: Optional[str]):
    """Initialize a new eval suite for a skill.
    
    SKILL_NAME: Name of the skill to create evals for
    """
    output_dir = Path(path) / skill_name
    
    # Check if user wants to generate from SKILL.md
    if not from_skill:
        has_skill_md = Confirm.ask(
            "Do you have a SKILL.md file to generate evals from?",
            default=False
        )
        if has_skill_md:
            from_skill = Prompt.ask(
                "Enter path or URL to SKILL.md",
                default=""
            )
    
    # If we have a skill source, use the generator
    if from_skill and from_skill.strip():
        _generate_from_skill(from_skill.strip(), output_dir, skill_name)
        return
    
    # Otherwise, create template structure
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create eval.yaml
    eval_yaml = f"""# Eval specification for {skill_name}
name: {skill_name}-eval
description: Evaluation suite for the {skill_name} skill
skill: {skill_name}
version: "1.0"

config:
  trials_per_task: 3
  timeout_seconds: 300
  parallel: false

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
    config:
      assertions:
        - "len(output) > 0"

tasks:
  - include: tasks/*.yaml
"""
    (output_dir / "eval.yaml").write_text(eval_yaml)
    
    # Create tasks directory
    tasks_dir = output_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    
    # Create example task
    example_task = f"""# Example task for {skill_name}
id: {skill_name}-example-001
name: Example Task
description: Example task to test {skill_name}

inputs:
  prompt: "Example prompt for the skill"
  context: {{}}

expected:
  outcomes:
    - type: task_completed
  output_contains:
    - "expected output"
"""
    (tasks_dir / "example-task.yaml").write_text(example_task)
    
    # Create graders directory
    graders_dir = output_dir / "graders"
    graders_dir.mkdir(exist_ok=True)
    
    # Create example grader script
    grader_script = '''#!/usr/bin/env python3
"""Example grader script for custom validation."""

import json
import sys


def grade(context: dict) -> dict:
    """Grade the skill execution.
    
    Args:
        context: Grading context with task, output, transcript, etc.
        
    Returns:
        dict with score, passed, message, and optional details
    """
    output = context.get("output", "")
    
    # Add your custom grading logic here
    score = 1.0 if output else 0.0
    
    return {
        "score": score,
        "passed": score >= 0.5,
        "message": "Custom grading complete",
        "details": {
            "output_length": len(output),
        },
    }


if __name__ == "__main__":
    # Read context from stdin
    context = json.load(sys.stdin)
    result = grade(context)
    print(json.dumps(result))
'''
    (graders_dir / "custom_grader.py").write_text(grader_script)
    
    # Create trigger tests file
    trigger_tests = f"""# Trigger accuracy tests for {skill_name}
skill: {skill_name}

should_trigger_prompts:
  - prompt: "Use {skill_name} to do something"
    reason: "Explicit skill mention"
  - prompt: "Help me with [relevant task]"
    reason: "Relevant task request"

should_not_trigger_prompts:
  - prompt: "What's the weather like?"
    reason: "Unrelated question"
  - prompt: "Help me with [unrelated task]"
    reason: "Different domain"
"""
    (output_dir / "trigger_tests.yaml").write_text(trigger_tests)
    
    console.print(f"[green]✓[/green] Created eval suite at: [bold]{output_dir}[/bold]")
    console.print()
    console.print("Structure created:")
    console.print(f"  {output_dir}/")
    console.print(f"  ├── eval.yaml")
    console.print(f"  ├── trigger_tests.yaml")
    console.print(f"  ├── tasks/")
    console.print(f"  │   └── example-task.yaml")
    console.print(f"  └── graders/")
    console.print(f"      └── custom_grader.py")
    console.print()
    console.print("Next steps:")
    console.print(f"  1. Edit [bold]tasks/*.yaml[/bold] to add test cases")
    console.print(f"  2. Edit [bold]trigger_tests.yaml[/bold] for trigger accuracy tests")
    console.print(f"  3. Run: [bold]skill-eval run {output_dir}/eval.yaml[/bold]")


def _generate_from_skill(source: str, output_dir: Path, skill_name: str):
    """Generate eval suite from a SKILL.md file."""
    from skill_eval.generator import SkillParser, EvalGenerator
    
    parser = SkillParser()
    
    console.print(f"[bold blue]Parsing SKILL.md...[/bold blue]")
    
    try:
        # Determine if source is URL or file path
        if source.startswith(("http://", "https://")):
            skill = parser.parse_url(source)
        else:
            skill = parser.parse_file(source)
        
        console.print(f"[green]✓[/green] Parsed skill: [bold]{skill.name}[/bold]")
        console.print(f"  Triggers found: {len(skill.triggers)}")
        console.print(f"  CLI commands: {', '.join(skill.cli_commands[:5]) or 'none'}")
        console.print(f"  Keywords: {', '.join(skill.keywords[:5]) or 'none'}")
        console.print()
        
    except Exception as e:
        console.print(f"[red]✗ Failed to parse SKILL.md:[/red] {e}")
        sys.exit(1)
    
    # Generate eval files
    generator = EvalGenerator(skill)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir = output_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    graders_dir = output_dir / "graders"
    graders_dir.mkdir(exist_ok=True)
    
    # Write eval.yaml
    eval_yaml = generator.generate_eval_yaml()
    (output_dir / "eval.yaml").write_text(eval_yaml)
    
    # Write trigger_tests.yaml
    trigger_tests = generator.generate_trigger_tests()
    (output_dir / "trigger_tests.yaml").write_text(trigger_tests)
    
    # Write example tasks
    tasks = generator.generate_example_tasks()
    for filename, content in tasks:
        (tasks_dir / filename).write_text(content)
    
    console.print(f"[green]✓[/green] Generated eval suite at: [bold]{output_dir}[/bold]")
    console.print()
    console.print("Structure created:")
    console.print(f"  {output_dir}/")
    console.print(f"  ├── eval.yaml [bold](auto-generated)[/bold]")
    console.print(f"  ├── trigger_tests.yaml [bold](auto-generated)[/bold]")
    console.print(f"  └── tasks/")
    for filename, _ in tasks:
        console.print(f"      └── {filename}")
    console.print()
    console.print("[yellow]Review and customize the generated files![/yellow]")
    console.print()
    console.print("Next steps:")
    console.print(f"  1. Review [bold]eval.yaml[/bold] graders and thresholds")
    console.print(f"  2. Add/edit [bold]tasks/*.yaml[/bold] test cases")
    console.print(f"  3. Run: [bold]skill-eval run {output_dir}/eval.yaml[/bold]")


@main.command()
@click.argument("skill_source", type=str)
@click.option("--output", "-o", type=click.Path(), help="Output directory (default: skill name)")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
def generate(skill_source: str, output: Optional[str], force: bool):
    """Generate eval suite from a SKILL.md file.
    
    SKILL_SOURCE: Path or URL to SKILL.md file
    
    Examples:
    
      skill-eval generate ./skills/azure-functions/SKILL.md
      
      skill-eval generate https://github.com/microsoft/GitHub-Copilot-for-Azure/blob/main/plugin/skills/azure-functions/SKILL.md
      
      skill-eval generate ./SKILL.md -o evals/my-skill
    """
    from skill_eval.generator import SkillParser, EvalGenerator
    
    parser = SkillParser()
    
    console.print(f"[bold blue]skill-eval[/bold blue] v{__version__}")
    console.print()
    console.print(f"Parsing: {skill_source[:80]}{'...' if len(skill_source) > 80 else ''}")
    
    try:
        # Determine if source is URL or file path
        if skill_source.startswith(("http://", "https://")):
            skill = parser.parse_url(skill_source)
        else:
            skill = parser.parse_file(skill_source)
        
        console.print(f"[green]✓[/green] Parsed skill: [bold]{skill.name}[/bold]")
        
        if skill.description:
            desc = skill.description[:150] + "..." if len(skill.description) > 150 else skill.description
            console.print(f"  Description: {desc}")
        
        console.print(f"  Triggers extracted: {len(skill.triggers)}")
        console.print(f"  Anti-triggers: {len(skill.anti_triggers)}")
        console.print(f"  CLI commands: {len(skill.cli_commands)}")
        console.print(f"  Keywords: {len(skill.keywords)}")
        console.print()
        
    except Exception as e:
        console.print(f"[red]✗ Failed to parse SKILL.md:[/red] {e}")
        sys.exit(1)
    
    # Determine output directory
    if output:
        output_dir = Path(output)
    else:
        safe_name = skill.name.lower().replace(' ', '-')
        safe_name = ''.join(c if c.isalnum() or c == '-' else '-' for c in safe_name)
        output_dir = Path(safe_name)
    
    # Check for existing files
    if output_dir.exists() and not force:
        if (output_dir / "eval.yaml").exists():
            overwrite = Confirm.ask(
                f"[yellow]eval.yaml already exists in {output_dir}. Overwrite?[/yellow]",
                default=False
            )
            if not overwrite:
                console.print("[yellow]Aborted.[/yellow]")
                return
    
    # Generate eval files
    generator = EvalGenerator(skill)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir = output_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    
    # Write eval.yaml
    eval_yaml = generator.generate_eval_yaml()
    (output_dir / "eval.yaml").write_text(eval_yaml)
    console.print(f"[green]✓[/green] Created eval.yaml")
    
    # Write trigger_tests.yaml
    trigger_tests = generator.generate_trigger_tests()
    (output_dir / "trigger_tests.yaml").write_text(trigger_tests)
    console.print(f"[green]✓[/green] Created trigger_tests.yaml")
    
    # Write example tasks
    tasks = generator.generate_example_tasks()
    for filename, content in tasks:
        (tasks_dir / filename).write_text(content)
        console.print(f"[green]✓[/green] Created tasks/{filename}")
    
    console.print()
    console.print(Panel(
        f"Generated eval suite at: [bold]{output_dir}[/bold]\n\n"
        f"Run with:\n"
        f"  [bold]skill-eval run {output_dir}/eval.yaml[/bold]\n\n"
        f"Or with real LLM:\n"
        f"  [bold]skill-eval run {output_dir}/eval.yaml --executor copilot-sdk[/bold]",
        title="[green]✓ Success[/green]",
        border_style="green"
    ))


@main.command()
@click.argument("results_path", type=click.Path(exists=True))
@click.option("--format", "-f", type=click.Choice(["json", "markdown", "github"]), default="markdown", help="Output format")
def report(results_path: str, format: str):
    """Generate a report from eval results.
    
    RESULTS_PATH: Path to results JSON file
    """
    from skill_eval.schemas.results import EvalResult
    
    result = EvalResult.from_file(results_path)
    
    if format == "json":
        reporter = JSONReporter()
        print(reporter.report(result))
    elif format == "markdown":
        reporter = MarkdownReporter()
        print(reporter.report(result))
    elif format == "github":
        reporter = GitHubReporter()
        print(reporter.report_summary(result))


@main.command()
def list_graders():
    """List available grader types."""
    from skill_eval.graders import GraderRegistry
    
    console.print("[bold]Available Grader Types[/bold]")
    console.print()
    
    graders = {
        "code": "Deterministic code-based assertions",
        "regex": "Pattern matching against output",
        "tool_calls": "Validate tool call patterns",
        "script": "Run external Python script",
        "llm": "LLM-as-judge with rubric",
        "llm_comparison": "Compare output to reference using LLM",
        "human": "Requires human review",
        "human_calibration": "Human calibration for LLM graders",
    }
    
    table = Table()
    table.add_column("Type", style="cyan")
    table.add_column("Description")
    
    for grader_type, description in graders.items():
        table.add_row(grader_type, description)
    
    console.print(table)


@main.command()
@click.argument("results_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--output", "-o", type=click.Path(), help="Output file path for comparison report")
@click.option("--format", "-f", type=click.Choice(["markdown", "json"]), default="markdown", help="Output format")
def compare(results_files: tuple[str, ...], output: Optional[str], format: str):
    """Compare results across multiple eval runs.
    
    Useful for comparing different models, versions, or configurations.
    
    RESULTS_FILES: Two or more results JSON files to compare
    """
    from skill_eval.schemas.results import EvalResult
    
    if len(results_files) < 2:
        console.print("[red]✗ Need at least 2 results files to compare[/red]")
        sys.exit(1)
    
    # Load all results
    results: list[EvalResult] = []
    for path in results_files:
        try:
            results.append(EvalResult.from_file(path))
        except Exception as e:
            console.print(f"[red]✗ Failed to load {path}:[/red] {e}")
            sys.exit(1)
    
    console.print(f"[bold blue]Model Comparison Report[/bold blue]")
    console.print()
    
    # Summary comparison table
    table = Table(title="Summary Comparison")
    table.add_column("Metric")
    for r in results:
        label = r.config.model or r.eval_name
        table.add_column(label[:20], justify="right")
    
    # Add rows
    table.add_row(
        "Pass Rate",
        *[f"{r.summary.pass_rate:.1%}" for r in results]
    )
    table.add_row(
        "Composite Score",
        *[f"{r.summary.composite_score:.2f}" for r in results]
    )
    table.add_row(
        "Tasks Passed",
        *[f"{r.summary.passed}/{r.summary.total_tasks}" for r in results]
    )
    table.add_row(
        "Duration",
        *[f"{r.summary.duration_ms}ms" for r in results]
    )
    table.add_row(
        "Executor",
        *[r.config.executor for r in results]
    )
    
    console.print(table)
    
    # Per-task comparison
    console.print()
    task_table = Table(title="Per-Task Comparison")
    task_table.add_column("Task")
    for r in results:
        label = r.config.model or r.eval_name
        task_table.add_column(label[:15], justify="center")
    
    # Get all task IDs
    all_task_ids = set()
    for r in results:
        for t in r.tasks:
            all_task_ids.add(t.id)
    
    for task_id in sorted(all_task_ids):
        row = [task_id[:30]]
        for r in results:
            task = next((t for t in r.tasks if t.id == task_id), None)
            if task:
                icon = "✅" if task.status == "passed" else "❌"
                score = task.aggregate.mean_score if task.aggregate else 0
                row.append(f"{icon} {score:.2f}")
            else:
                row.append("-")
        task_table.add_row(*row)
    
    console.print(task_table)
    
    # Identify winner
    best_idx = max(range(len(results)), key=lambda i: results[i].summary.composite_score)
    best = results[best_idx]
    console.print()
    console.print(f"[green]🏆 Best: {best.config.model or best.eval_name} (score: {best.summary.composite_score:.2f})[/green]")
    
    # Output to file
    if output:
        if format == "markdown":
            report = _generate_comparison_markdown(results)
            Path(output).write_text(report)
        elif format == "json":
            import json
            comparison = {
                "results": [r.model_dump() for r in results],
                "best_model": best.config.model,
                "best_score": best.summary.composite_score,
            }
            Path(output).write_text(json.dumps(comparison, indent=2, default=str))
        console.print(f"\n[green]✓[/green] Comparison written to: {output}")


@main.command()
@click.argument("telemetry_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for analysis")
@click.option("--skill", "-s", type=str, help="Filter to specific skill")
def analyze(telemetry_path: str, output: Optional[str], skill: Optional[str]):
    """Analyze runtime telemetry data.
    
    Convert captured session telemetry into eval-compatible format for analysis.
    
    TELEMETRY_PATH: Path to telemetry JSON file or directory
    """
    from skill_eval.telemetry import TelemetryAnalyzer
    
    try:
        analyzer = TelemetryAnalyzer()
        analysis = analyzer.analyze_file(telemetry_path, skill_filter=skill)
        
        console.print(f"[bold blue]Runtime Telemetry Analysis[/bold blue]")
        console.print()
        console.print(f"Sessions analyzed: {analysis.get('total_sessions', 0)}")
        console.print(f"Skills invoked: {', '.join(analysis.get('skills', []))}")
        console.print()
        
        # Show metrics
        if "metrics" in analysis:
            table = Table(title="Runtime Metrics")
            table.add_column("Metric")
            table.add_column("Value", justify="right")
            
            for name, value in analysis["metrics"].items():
                table.add_row(name, str(value))
            
            console.print(table)
        
        if output:
            import json
            Path(output).write_text(json.dumps(analysis, indent=2, default=str))
            console.print(f"\n[green]✓[/green] Analysis written to: {output}")
            
    except ImportError:
        console.print("[yellow]⚠ Telemetry analysis requires additional setup[/yellow]")
        console.print("See docs/TELEMETRY.md for configuration instructions")
    except Exception as e:
        console.print(f"[red]✗ Analysis failed:[/red] {e}")
        sys.exit(1)


def _generate_comparison_markdown(results: list) -> str:
    """Generate markdown comparison report."""
    lines = ["# Model Comparison Report", ""]
    
    # Summary table
    lines.append("## Summary")
    lines.append("")
    headers = ["Metric"] + [r.config.model or r.eval_name for r in results]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    lines.append("| Pass Rate | " + " | ".join([f"{r.summary.pass_rate:.1%}" for r in results]) + " |")
    lines.append("| Composite Score | " + " | ".join([f"{r.summary.composite_score:.2f}" for r in results]) + " |")
    lines.append("| Tasks Passed | " + " | ".join([f"{r.summary.passed}/{r.summary.total_tasks}" for r in results]) + " |")
    lines.append("")
    
    # Per-task table
    lines.append("## Per-Task Results")
    lines.append("")
    
    all_task_ids = set()
    for r in results:
        for t in r.tasks:
            all_task_ids.add(t.id)
    
    headers = ["Task"] + [r.config.model or r.eval_name for r in results]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for task_id in sorted(all_task_ids):
        row = [task_id]
        for r in results:
            task = next((t for t in r.tasks if t.id == task_id), None)
            if task:
                icon = "✅" if task.status == "passed" else "❌"
                row.append(icon)
            else:
                row.append("-")
        lines.append("| " + " | ".join(row) + " |")
    
    return "\n".join(lines)


def _display_results(result, verbose: bool = False):
    """Display results in the console."""
    # Summary panel
    status = "✅ PASSED" if result.summary.pass_rate >= 0.8 else "❌ FAILED"
    status_color = "green" if result.summary.pass_rate >= 0.8 else "red"
    
    summary_text = f"""[bold]{status}[/bold]

Pass Rate: {result.summary.pass_rate:.1%} ({result.summary.passed}/{result.summary.total_tasks})
Composite Score: {result.summary.composite_score:.2f}
Duration: {result.summary.duration_ms}ms
"""
    
    console.print(Panel(summary_text, title=f"[{status_color}]{result.eval_name}[/{status_color}]", border_style=status_color))

    # Metrics table
    if result.metrics:
        console.print()
        table = Table(title="Metrics")
        table.add_column("Metric")
        table.add_column("Score", justify="right")
        table.add_column("Threshold", justify="right")
        table.add_column("Weight", justify="right")
        table.add_column("Status")
        
        for name, metric in result.metrics.items():
            status_icon = "✅" if metric.passed else "❌"
            table.add_row(
                name, 
                f"{metric.score:.2f}", 
                f"{metric.threshold:.2f}",
                f"{metric.weight:.1f}",
                status_icon
            )
        
        console.print(table)

    # Task results table
    console.print()
    table = Table(title="Task Results")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Score", justify="right")
    table.add_column("Duration", justify="right")
    if verbose:
        table.add_column("Tool Calls", justify="right")
        table.add_column("Tokens", justify="right")
    
    status_icons = {"passed": "✅", "failed": "❌", "partial": "⚠️", "error": "💥"}
    
    for task in result.tasks:
        icon = status_icons.get(task.status, "❓")
        score = f"{task.aggregate.mean_score:.2f}" if task.aggregate else "-"
        duration = f"{task.aggregate.mean_duration_ms}ms" if task.aggregate else "-"
        
        if verbose:
            # Get tool calls and tokens from first trial
            tool_calls = "-"
            tokens = "-"
            if task.trials:
                trial = task.trials[0]
                if trial.transcript_summary:
                    tool_calls = str(trial.transcript_summary.tool_calls)
                    tokens = str(trial.transcript_summary.tokens_total) if trial.transcript_summary.tokens_total else "-"
            table.add_row(task.name[:35], icon, score, duration, tool_calls, tokens)
        else:
            table.add_row(task.name[:40], icon, score, duration)
    
    console.print(table)
    
    # Verbose: Show detailed task info including prompts and responses
    if verbose and result.tasks:
        console.print()
        console.print("[bold]Task Details[/bold]")
        console.print()
        
        for task in result.tasks:
            # Task header
            status_icon = status_icons.get(task.status, "❓")
            console.print(f"[bold]{status_icon} {task.name}[/bold] (id: {task.id})")
            
            for trial in task.trials:
                console.print(f"  [dim]Trial {trial.trial_id}:[/dim] {trial.status} | score: {trial.score:.2f} | {trial.duration_ms}ms")
                
                # Show transcript summary
                if trial.transcript_summary:
                    ts = trial.transcript_summary
                    if ts.tools_used:
                        console.print(f"    [dim]Tools:[/dim] {', '.join(ts.tools_used[:5])}")
                    if ts.errors:
                        console.print(f"    [red]Errors:[/red] {', '.join(ts.errors[:3])}")
                
                # Show conversation/transcript
                if trial.transcript:
                    console.print("    [dim]Conversation:[/dim]")
                    for i, turn in enumerate(trial.transcript[:6]):  # Show first 6 turns
                        role = turn.get("role", "unknown")
                        content = turn.get("content", "")[:200]  # Truncate
                        if role == "user":
                            console.print(f"      [cyan]User:[/cyan] {content}")
                        elif role == "assistant":
                            console.print(f"      [green]Assistant:[/green] {content}...")
                        elif role == "tool":
                            tool_name = turn.get("name", "tool")
                            console.print(f"      [yellow]Tool ({tool_name}):[/yellow] {content[:100]}...")
                    if len(trial.transcript) > 6:
                        console.print(f"      [dim]... and {len(trial.transcript) - 6} more turns[/dim]")
                
                # Show grader results
                if trial.grader_results:
                    console.print("    [dim]Graders:[/dim]")
                    for name, gr in trial.grader_results.items():
                        gr_icon = "✅" if gr.passed else "❌"
                        console.print(f"      {gr_icon} {name}: {gr.score:.2f} - {gr.message[:60]}")
                
                # Show output snippet
                if trial.output:
                    output_preview = trial.output[:300].replace('\n', ' ')
                    console.print(f"    [dim]Output:[/dim] {output_preview}...")
                
                if trial.error:
                    console.print(f"    [red]Error:[/red] {trial.error}")
                
                console.print()


if __name__ == "__main__":
    main()
