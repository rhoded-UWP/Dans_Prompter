# AGENTS.md

## Project conventions

- Keep application code in `src/dans_teleprompter/`.
- Keep automated tests in `tests/`.
- Add or update tests when behavior changes.
- Run the test suite before finalizing changes.

# Codex Instructions

Read README_Codex_Improvements.md before making architectural decisions.

Implement only the milestone requested in the current task.

Do not add placeholder implementations for later milestones.

Run relevant tests before declaring a task complete.

Do not change established behavior without identifying the conflicting specification.

Keep the GUI, audio processing, and application controller separated.

Never access PySide6 widgets from a worker thread.

Prefer simple, deterministic implementations over speculative abstractions.

At the end of each task, report:
1. Files changed
2. Tests run
3. Manual testing required
4. Known limitations
5. Recommended next step