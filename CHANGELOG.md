# Changelog

All notable changes to skill-eval will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.2] - 2026-02-01

### Added

- `--suggestions-file` option to save improvement suggestions to markdown file
- Improved progress display with step-by-step status (tool counts, activity indicators)
- Copilot SDK usage guide in AGENTS.md

### Fixed

- Fixed Copilot SDK import (`from copilot import CopilotClient` not `copilot_sdk`)
- Fixed Windows glob pattern in release workflow
- Fixed linting issues across codebase (import sorting, exception chaining, etc.)
- Clarified fixture isolation between tasks (each task gets fresh temp workspace)

## [0.0.1] - 2026-02-01

### Added

- **CLI Commands**
  - `skill-eval run` - Run evaluation suites against skills
  - `skill-eval generate` - Auto-generate evals from SKILL.md files
  - `skill-eval init` - Initialize new eval suites interactively
  - `skill-eval report` - Generate reports from results

- **Eval Generation**
  - Pattern-based generation from SKILL.md files
  - LLM-assisted generation with `--assist` flag for better tasks/fixtures
  - Support for multiple models (Claude, GPT-4, etc.)

- **Executors**
  - Mock executor for testing without LLM calls
  - Copilot SDK executor for real integration testing

- **Graders**
  - Code graders with Python assertions
  - Regex graders for pattern matching
  - LLM graders for semantic evaluation

- **Features**
  - Real-time progress display with conversation streaming (`-v`)
  - Transcript logging (`--log`)
  - Project context support (`--context-dir`)
  - LLM-powered improvement suggestions (`--suggestions`)

- **Documentation**
  - Comprehensive README with examples
  - Tutorial guide
  - Grader reference
  - Demo script for walkthroughs

### Fixed

- Grader eval context now includes `str`, `int`, `bool`, etc.
- Transcript normalization for proper tool call detection
- YAML escaping for regex patterns with backslashes
- Progress bar now shows 100% on completion

[Unreleased]: https://github.com/spboyer/evals-for-skills/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/spboyer/evals-for-skills/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/spboyer/evals-for-skills/releases/tag/v0.0.1
