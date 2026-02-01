"""Tests for waza graders."""

import pytest

from waza.graders.base import GraderContext, GraderRegistry
from waza.graders.code_graders import CodeGrader, RegexGrader, ToolCallGrader


class TestCodeGrader:
    """Tests for CodeGrader."""

    def test_passing_assertions(self):
        """Test grader with passing assertions."""
        grader = CodeGrader(
            name="test",
            config={"assertions": ["len(output) > 0", "'hello' in output.lower()"]},
        )
        context = GraderContext(
            task={"id": "test"},
            output="Hello, World!",
        )
        result = grader.grade(context)
        assert result.passed is True
        assert result.score == 1.0

    def test_failing_assertions(self):
        """Test grader with failing assertions."""
        grader = CodeGrader(
            name="test",
            config={"assertions": ["len(output) > 100"]},
        )
        context = GraderContext(
            task={"id": "test"},
            output="Short",
        )
        result = grader.grade(context)
        assert result.passed is False
        assert result.score == 0.0

    def test_partial_pass(self):
        """Test grader with partial pass."""
        grader = CodeGrader(
            name="test",
            config={"assertions": ["True", "False"]},
        )
        context = GraderContext(task={"id": "test"}, output="test")
        result = grader.grade(context)
        assert result.passed is False
        assert result.score == 0.5


class TestRegexGrader:
    """Tests for RegexGrader."""

    def test_must_match(self):
        """Test regex must_match."""
        grader = RegexGrader(
            name="test",
            config={"must_match": [r"hello", r"\d+"]},
        )
        context = GraderContext(
            task={"id": "test"},
            output="hello world 123",
        )
        result = grader.grade(context)
        assert result.passed is True

    def test_must_not_match(self):
        """Test regex must_not_match."""
        grader = RegexGrader(
            name="test",
            config={"must_not_match": [r"error", r"fail"]},
        )
        context = GraderContext(
            task={"id": "test"},
            output="success",
        )
        result = grader.grade(context)
        assert result.passed is True

    def test_forbidden_found(self):
        """Test regex finding forbidden pattern."""
        grader = RegexGrader(
            name="test",
            config={"must_not_match": [r"error"]},
        )
        context = GraderContext(
            task={"id": "test"},
            output="An error occurred",
        )
        result = grader.grade(context)
        assert result.passed is False


class TestToolCallGrader:
    """Tests for ToolCallGrader."""

    def test_required_tools(self):
        """Test required tool call patterns."""
        grader = ToolCallGrader(
            name="test",
            config={"required": [{"pattern": "azd"}]},
        )
        context = GraderContext(
            task={"id": "test"},
            transcript=[
                {"type": "tool_call", "tool": "azd", "args": {"cmd": "up"}},
            ],
        )
        result = grader.grade(context)
        assert result.passed is True

    def test_forbidden_tools(self):
        """Test forbidden tool call patterns."""
        grader = ToolCallGrader(
            name="test",
            config={"forbidden": [{"pattern": "rm -rf"}]},
        )
        context = GraderContext(
            task={"id": "test"},
            transcript=[
                {"type": "tool_call", "tool": "bash", "args": {"cmd": "rm -rf /"}},
            ],
        )
        result = grader.grade(context)
        assert result.passed is False


class TestGraderRegistry:
    """Tests for GraderRegistry."""

    def test_create_grader(self):
        """Test creating grader from registry."""
        grader = GraderRegistry.create(
            grader_type="code",
            name="test",
            config={"assertions": ["True"]},
        )
        assert isinstance(grader, CodeGrader)

    def test_list_types(self):
        """Test listing grader types."""
        types = GraderRegistry.list_types()
        assert "code" in types
        assert "regex" in types
        assert "llm" in types

    def test_unknown_type(self):
        """Test creating unknown grader type."""
        with pytest.raises(ValueError):
            GraderRegistry.create("unknown_type", "test")
