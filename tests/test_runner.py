"""Tests for waza runner."""

import tempfile
from pathlib import Path

<<<<<<< HEAD
from skill_eval.runner import EvalRunner
from skill_eval.schemas.eval_spec import EvalSpec, GraderConfig, GraderType
from skill_eval.schemas.task import Task, TaskInput
=======
from waza.runner import EvalRunner
from waza.schemas.eval_spec import EvalSpec, GraderConfig, GraderType
from waza.schemas.task import Task, TaskInput
>>>>>>> refs/remotes/origin/main


class TestEvalRunner:
    """Tests for EvalRunner."""

    def test_run_with_mock_executor(self):
        """Test running eval with mock executor."""
        spec = EvalSpec(
            name="test-eval",
            skill="test-skill",
            graders=[
                GraderConfig(
                    type=GraderType.CODE,
                    name="basic",
                    config={"assertions": ["len(output) > 0"]},
                )
            ],
        )

        tasks = [
            Task(id="test-001", name="Test Task", inputs=TaskInput(prompt="Test")),
        ]

        runner = EvalRunner(spec=spec)
        result = runner.run(tasks)

        assert result.eval_id.startswith("test-eval-")
        assert result.skill == "test-skill"
        assert result.summary.total_tasks == 1
        assert result.summary.pass_rate > 0  # Mock executor produces output

    def test_run_parallel(self):
        """Test running eval in parallel mode."""
        spec = EvalSpec(
            name="test-eval",
            skill="test-skill",
        )
        spec.config.parallel = True
        spec.config.max_workers = 2

        tasks = [
            Task(id="test-001", name="Task 1", inputs=TaskInput(prompt="Test 1")),
            Task(id="test-002", name="Task 2", inputs=TaskInput(prompt="Test 2")),
        ]

        runner = EvalRunner(spec=spec)
        result = runner.run(tasks)

        assert result.summary.total_tasks == 2

    def test_multiple_trials(self):
        """Test running multiple trials per task."""
        spec = EvalSpec(
            name="test-eval",
            skill="test-skill",
        )
        spec.config.trials_per_task = 3

        tasks = [
            Task(id="test-001", name="Test Task", inputs=TaskInput(prompt="Test")),
        ]

        runner = EvalRunner(spec=spec)
        result = runner.run(tasks)

        assert len(result.tasks[0].trials) == 3

    def test_composite_score(self):
        """Test composite score calculation."""
        spec = EvalSpec(
            name="test-eval",
            skill="test-skill",
        )

        # Add metrics to spec
        from waza.schemas.eval_spec import MetricConfig
        spec.metrics = [
            MetricConfig(name="task_completion", weight=0.5, threshold=0.8),
            MetricConfig(name="behavior_quality", weight=0.5, threshold=0.7),
        ]

        tasks = [
            Task(id="test-001", name="Task 1", inputs=TaskInput(prompt="Test 1")),
            Task(id="test-002", name="Task 2", inputs=TaskInput(prompt="Test 2")),
        ]

        runner = EvalRunner(spec=spec)
        result = runner.run(tasks)

        assert 0 <= result.summary.composite_score <= 1

    def test_load_tasks_from_files(self):
        """Test loading tasks from YAML files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create task file
            task_yaml = """
id: file-task-001
name: File Task
inputs:
  prompt: Test from file
"""
            tasks_dir = Path(tmpdir) / "tasks"
            tasks_dir.mkdir()
            (tasks_dir / "test.yaml").write_text(task_yaml)

            spec = EvalSpec(
                name="test-eval",
                skill="test-skill",
                tasks=["tasks/*.yaml"],
            )

            runner = EvalRunner(spec=spec, base_path=Path(tmpdir))
            tasks = runner.load_tasks()

            assert len(tasks) == 1
            assert tasks[0].id == "file-task-001"
