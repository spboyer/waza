"""Tests for waza schemas."""


from waza.schemas.eval_spec import EvalConfig, EvalSpec, GraderConfig, GraderType, MetricConfig
from waza.schemas.results import EvalResult, EvalSummary, GraderResult, TaskResult, TrialResult
from waza.schemas.task import Task, TaskExpected, TaskInput, TriggerTestSuite


class TestEvalSpec:
    """Tests for EvalSpec schema."""

    def test_minimal_spec(self):
        """Test creating a minimal eval spec."""
        spec = EvalSpec(name="test-eval", skill="test-skill")
        assert spec.name == "test-eval"
        assert spec.skill == "test-skill"
        assert spec.version == "1.0"
        assert spec.config.trials_per_task == 1

    def test_full_spec(self):
        """Test creating a full eval spec."""
        spec = EvalSpec(
            name="test-eval",
            description="Test evaluation",
            skill="test-skill",
            version="2.0",
            config=EvalConfig(trials_per_task=5, timeout_seconds=600, parallel=True),
            metrics=[
                MetricConfig(name="task_completion", weight=0.5, threshold=0.8),
                MetricConfig(name="trigger_accuracy", weight=0.5, threshold=0.9),
            ],
            graders=[
                GraderConfig(type=GraderType.CODE, name="basic", config={"assertions": ["True"]}),
            ],
            tasks=["tasks/*.yaml"],
        )
        assert spec.config.trials_per_task == 5
        assert len(spec.metrics) == 2
        assert len(spec.graders) == 1

    def test_from_yaml(self):
        """Test parsing eval spec from YAML."""
        yaml_content = """
name: test-eval
skill: test-skill
config:
  trials_per_task: 3
metrics:
  - name: task_completion
    weight: 1.0
    threshold: 0.8
tasks:
  - "tasks/*.yaml"
"""
        spec = EvalSpec.from_yaml(yaml_content)
        assert spec.name == "test-eval"
        assert spec.config.trials_per_task == 3


class TestTask:
    """Tests for Task schema."""

    def test_minimal_task(self):
        """Test creating a minimal task."""
        task = Task(
            id="test-001",
            name="Test Task",
            inputs=TaskInput(prompt="Test prompt"),
        )
        assert task.id == "test-001"
        assert task.inputs.prompt == "Test prompt"
        assert task.enabled is True

    def test_full_task(self):
        """Test creating a full task."""
        task = Task(
            id="test-001",
            name="Test Task",
            description="A test task",
            inputs=TaskInput(
                prompt="Test prompt",
                context={"key": "value"},
                environment={"VAR": "value"},
            ),
            expected=TaskExpected(
                output_contains=["expected"],
                output_not_contains=["error"],
            ),
            tags=["unit", "fast"],
        )
        assert task.description == "A test task"
        assert task.inputs.context["key"] == "value"
        assert "expected" in task.expected.output_contains


class TestTriggerTestSuite:
    """Tests for TriggerTestSuite schema."""

    def test_trigger_suite(self):
        """Test creating a trigger test suite."""
        yaml_content = """
skill: test-skill
should_trigger_prompts:
  - prompt: "Use test-skill"
    should_trigger: true
    reason: "Explicit mention"
should_not_trigger_prompts:
  - prompt: "Random question"
    should_trigger: false
    reason: "Unrelated"
"""
        suite = TriggerTestSuite.from_yaml(yaml_content)
        assert suite.skill == "test-skill"
        assert len(suite.should_trigger_prompts) == 1
        assert len(suite.should_not_trigger_prompts) == 1


class TestResults:
    """Tests for result schemas."""

    def test_grader_result(self):
        """Test creating a grader result."""
        result = GraderResult(
            name="test_grader",
            type="code",
            score=0.9,
            passed=True,
            message="All assertions passed",
        )
        assert result.score == 0.9
        assert result.passed is True

    def test_trial_result(self):
        """Test creating a trial result."""
        trial = TrialResult(
            trial_id=1,
            status="passed",
            duration_ms=1000,
            grader_results={
                "test": GraderResult(name="test", type="code", score=1.0, passed=True)
            },
            output="Test output",
        )
        assert trial.score == 1.0
        assert trial.passed is True

    def test_task_result_aggregate(self):
        """Test task result aggregation."""
        task_result = TaskResult(
            id="test-001",
            name="Test Task",
            status="passed",
            trials=[
                TrialResult(trial_id=1, status="passed", grader_results={
                    "g1": GraderResult(name="g1", type="code", score=1.0, passed=True)
                }),
                TrialResult(trial_id=2, status="passed", grader_results={
                    "g1": GraderResult(name="g1", type="code", score=0.8, passed=True)
                }),
            ],
        )
        task_result.compute_aggregate()
        assert task_result.aggregate is not None
        assert task_result.aggregate.pass_rate == 1.0
        assert task_result.aggregate.mean_score == 0.9

    def test_eval_result_serialization(self):
        """Test eval result JSON serialization."""
        result = EvalResult(
            eval_id="test-001",
            skill="test-skill",
            eval_name="test-eval",
            summary=EvalSummary(
                total_tasks=10,
                passed=8,
                failed=2,
                pass_rate=0.8,
                composite_score=0.82,
            ),
        )
        json_str = result.to_json()
        assert "test-001" in json_str
        assert "test-skill" in json_str

        # Round-trip
        loaded = EvalResult.from_json(json_str)
        assert loaded.eval_id == result.eval_id
        assert loaded.summary.pass_rate == 0.8
