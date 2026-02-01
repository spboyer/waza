"""Runtime telemetry collection and analysis for skill evaluation.

This module provides tools for:
1. Collecting telemetry during live skill execution
2. Analyzing captured session data
3. Converting telemetry to eval-compatible format
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class TelemetryEvent:
    """A single telemetry event from skill execution."""

    timestamp: datetime
    event_type: str
    skill_name: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "skill_name": self.skill_name,
            "data": self.data,
            "session_id": self.session_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TelemetryEvent:
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=data["event_type"],
            skill_name=data.get("skill_name"),
            data=data.get("data", {}),
            session_id=data.get("session_id"),
        )


@dataclass
class SessionTelemetry:
    """Telemetry for a complete skill session."""

    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    skill_name: str | None = None
    prompt: str = ""
    output: str = ""
    events: list[TelemetryEvent] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        if self.end_time and self.start_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "skill_name": self.skill_name,
            "prompt": self.prompt,
            "output": self.output,
            "events": [e.to_dict() for e in self.events],
            "tool_calls": self.tool_calls,
            "success": self.success,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionTelemetry:
        return cls(
            session_id=data["session_id"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            skill_name=data.get("skill_name"),
            prompt=data.get("prompt", ""),
            output=data.get("output", ""),
            events=[TelemetryEvent.from_dict(e) for e in data.get("events", [])],
            tool_calls=data.get("tool_calls", []),
            success=data.get("success", True),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


class RuntimeCollector:
    """Collects telemetry during live skill execution.

    Usage:
        collector = RuntimeCollector()

        # Start session
        session_id = collector.start_session(prompt="Deploy to Azure")

        # Record events as they happen
        collector.record_event(session_id, "skill.invoked", skill_name="azure-deploy")
        collector.record_event(session_id, "tool.called", data={"tool": "az"})

        # End session
        collector.end_session(session_id, output="Deployed successfully", success=True)

        # Export for analysis
        collector.export_to_file("telemetry.json")
    """

    def __init__(self):
        self._sessions: dict[str, SessionTelemetry] = {}
        self._completed: list[SessionTelemetry] = []

    def start_session(
        self,
        prompt: str,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Start a new telemetry session."""
        import uuid

        session_id = session_id or str(uuid.uuid4())

        session = SessionTelemetry(
            session_id=session_id,
            start_time=datetime.utcnow(),
            prompt=prompt,
            metadata=metadata or {},
        )

        self._sessions[session_id] = session
        return session_id

    def record_event(
        self,
        session_id: str,
        event_type: str,
        skill_name: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Record an event in the session."""
        if session_id not in self._sessions:
            return

        session = self._sessions[session_id]

        event = TelemetryEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            skill_name=skill_name,
            data=data or {},
            session_id=session_id,
        )

        session.events.append(event)

        # Track skill if provided
        if skill_name and not session.skill_name:
            session.skill_name = skill_name

        # Track tool calls
        if event_type == "tool.called" and data:
            session.tool_calls.append(data)

    def end_session(
        self,
        session_id: str,
        output: str = "",
        success: bool = True,
        error: str | None = None,
    ) -> SessionTelemetry | None:
        """End a session and return the completed telemetry."""
        if session_id not in self._sessions:
            return None

        session = self._sessions.pop(session_id)
        session.end_time = datetime.utcnow()
        session.output = output
        session.success = success
        session.error = error

        self._completed.append(session)
        return session

    def get_session(self, session_id: str) -> SessionTelemetry | None:
        """Get a session by ID."""
        return self._sessions.get(session_id) or next(
            (s for s in self._completed if s.session_id == session_id), None
        )

    def export_to_file(self, path: str) -> None:
        """Export all completed sessions to a JSON file."""
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "sessions": [s.to_dict() for s in self._completed],
        }
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load_from_file(cls, path: str) -> list[SessionTelemetry]:
        """Load sessions from an exported file."""
        data = json.loads(Path(path).read_text())
        return [SessionTelemetry.from_dict(s) for s in data.get("sessions", [])]


class TelemetryAnalyzer:
    """Analyzes telemetry data and converts to eval format."""

    def analyze_file(
        self,
        path: str,
        skill_filter: str | None = None,
    ) -> dict[str, Any]:
        """Analyze a telemetry file."""
        sessions = RuntimeCollector.load_from_file(path)
        return self.analyze_sessions(sessions, skill_filter)

    def analyze_sessions(
        self,
        sessions: list[SessionTelemetry],
        skill_filter: str | None = None,
    ) -> dict[str, Any]:
        """Analyze a list of sessions."""
        # Filter by skill if specified
        if skill_filter:
            sessions = [s for s in sessions if s.skill_name == skill_filter]

        if not sessions:
            return {
                "total_sessions": 0,
                "skills": [],
                "metrics": {},
            }

        # Aggregate metrics
        skills = list({s.skill_name for s in sessions if s.skill_name})
        success_count = sum(1 for s in sessions if s.success)
        total_duration = sum(s.duration_ms for s in sessions)
        total_tool_calls = sum(len(s.tool_calls) for s in sessions)

        # Per-skill breakdown
        skill_stats: dict[str, dict[str, Any]] = {}
        for skill in skills:
            skill_sessions = [s for s in sessions if s.skill_name == skill]
            skill_stats[skill] = {
                "invocations": len(skill_sessions),
                "success_rate": sum(1 for s in skill_sessions if s.success) / len(skill_sessions),
                "avg_duration_ms": sum(s.duration_ms for s in skill_sessions) / len(skill_sessions),
                "total_tool_calls": sum(len(s.tool_calls) for s in skill_sessions),
            }

        return {
            "total_sessions": len(sessions),
            "skills": skills,
            "metrics": {
                "success_rate": success_count / len(sessions),
                "avg_duration_ms": total_duration / len(sessions),
                "total_tool_calls": total_tool_calls,
                "avg_tool_calls_per_session": total_tool_calls / len(sessions),
            },
            "skill_breakdown": skill_stats,
            "time_range": {
                "start": min(s.start_time for s in sessions).isoformat(),
                "end": max(s.end_time for s in sessions if s.end_time).isoformat() if any(s.end_time for s in sessions) else None,
            },
        }

    def to_eval_input(
        self,
        session: SessionTelemetry,
    ) -> dict[str, Any]:
        """Convert a session to eval task input format."""
        return {
            "id": f"runtime-{session.session_id}",
            "name": f"Runtime session {session.session_id[:8]}",
            "description": f"Captured from runtime on {session.start_time.isoformat()}",
            "inputs": {
                "prompt": session.prompt,
                "context": session.metadata,
            },
            "captured": {
                "output": session.output,
                "tool_calls": session.tool_calls,
                "events": [e.to_dict() for e in session.events],
                "duration_ms": session.duration_ms,
                "success": session.success,
                "error": session.error,
            },
        }
