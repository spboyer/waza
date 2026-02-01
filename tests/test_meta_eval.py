"""Tests for meta-evaluation (eval-as-skill) capability."""

from pathlib import Path

import pytest

from waza.runner import EvalRunner
from waza.schemas.eval_spec import EvalSpec
from waza.schemas.task import Task, TaskInput


class TestMetaEvaluation:
    """Tests for evaluating the waza-runner skill itself."""

    def test_waza_runner_skill_exists(self):
        """Verify the waza-runner SKILL.md exists and is valid."""
        skill_path = Path(__file__).parent.parent / "waza-runner" / "SKILL.md"
        assert skill_path.exists(), "waza-runner/SKILL.md should exist"

        content = skill_path.read_text()
        assert "---" in content, "Should have frontmatter"
        assert "name: waza-runner" in content
        assert "description:" in content

    def test_waza_runner_references(self):
        """Verify reference documentation exists."""
        refs_path = Path(__file__).parent.parent / "waza-runner" / "references"
        assert refs_path.exists(), "references/ directory should exist"

        eval_spec_ref = refs_path / "EVAL-SPEC.md"
        assert eval_spec_ref.exists(), "EVAL-SPEC.md reference should exist"

    def test_can_evaluate_eval_runner_skill(self):
        """Test that we can create an eval for the waza-runner itself."""
        spec = EvalSpec(
            name="waza-runner-meta-eval",
            description="Meta-evaluation of the waza-runner skill",
            skill="waza-runner",
            graders=[],
        )

        # Create a meta-task: asking the eval skill to run evals
        tasks = [
            Task(
                id="meta-eval-001",
                name="Run Eval on Example Skill",
                inputs=TaskInput(
                    prompt="Run evals on the azure-deploy skill",
                    context={"skill_to_eval": "azure-deploy"},
                ),
            ),
        ]

        runner = EvalRunner(spec=spec)
        result = runner.run(tasks)

        assert result.eval_id.startswith("waza-runner-meta-eval")
        assert result.skill == "waza-runner"
        assert result.summary.total_tasks == 1

    def test_eval_runner_can_evaluate_itself(self):
        """Recursive test: eval-runner evaluating itself."""
        spec = EvalSpec(
            name="recursive-meta-eval",
            skill="waza-runner",
        )

        tasks = [
            Task(
                id="recursive-001",
                name="Recursive Self-Eval",
                inputs=TaskInput(
                    prompt="Evaluate the waza-runner skill for quality",
                ),
            ),
        ]

        runner = EvalRunner(spec=spec)
        result = runner.run(tasks)

        # The mock executor will produce output, proving the pipeline works
        assert result.summary.total_tasks == 1
        assert len(result.tasks) == 1
        assert result.tasks[0].trials[0].output is not None


class TestExampleEvals:
    """Tests that example evals can be loaded and run."""

    def test_azure_deploy_eval_loads(self):
        """Test that azure-deploy eval spec loads correctly."""
        eval_path = Path(__file__).parent.parent / "examples" / "azure-deploy" / "eval.yaml"
        if not eval_path.exists():
            pytest.skip("azure-deploy example not found")

        spec = EvalSpec.from_file(str(eval_path))
        assert spec.name == "azure-deploy-eval"
        assert spec.skill == "azure-deploy"
        assert len(spec.metrics) == 3

    def test_azure_deploy_eval_runs(self):
        """Test that azure-deploy eval can execute."""
        eval_path = Path(__file__).parent.parent / "examples" / "azure-deploy" / "eval.yaml"
        if not eval_path.exists():
            pytest.skip("azure-deploy example not found")

        spec = EvalSpec.from_file(str(eval_path))
        runner = EvalRunner(spec=spec, base_path=eval_path.parent)

        tasks = runner.load_tasks()
        assert len(tasks) >= 2, "Should have at least 2 tasks"

        result = runner.run(tasks)
        assert result.summary.total_tasks >= 2

    def test_cli_recorder_eval_loads(self):
        """Test that cli-session-recorder eval spec loads correctly."""
        eval_path = Path(__file__).parent.parent / "examples" / "cli-session-recorder" / "eval.yaml"
        if not eval_path.exists():
            pytest.skip("cli-session-recorder example not found")

        spec = EvalSpec.from_file(str(eval_path))
        assert spec.name == "cli-session-recorder-eval"
        assert spec.skill == "cli-session-recorder"

    def test_cli_recorder_eval_runs(self):
        """Test that cli-session-recorder eval can execute."""
        eval_path = Path(__file__).parent.parent / "examples" / "cli-session-recorder" / "eval.yaml"
        if not eval_path.exists():
            pytest.skip("cli-session-recorder example not found")

        spec = EvalSpec.from_file(str(eval_path))
        runner = EvalRunner(spec=spec, base_path=eval_path.parent)

        tasks = runner.load_tasks()
        assert len(tasks) >= 2

        result = runner.run(tasks)
        assert result.summary.total_tasks >= 2
