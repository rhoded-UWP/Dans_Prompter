# Dan's Teleprompter Version 1 Plan

This plan is based on the current, narrowed specification in `README_Codex_Improvements(1).md`. Version 1 is a Windows 10/11 desktop application with two windows, offline `faster-whisper` voice tracking, constant-speed fallback, deterministic manual vamp mode, external `.txt`/`.docx` scripts, retake controls, optional local diagnostics, and a Windows installer.

Explicitly excluded from this plan are Ollama, all LLM features, semantic alignment rescue, automatic or spoken vamp/resume cues, transcript export, captions, cloud services, audio feedback, and other items listed as non-goals in the current specification.

## 1. Proposed module structure

```text
src/dans_teleprompter/
├── __init__.py
├── __main__.py                 # Process entry point only
├── app.py                      # Qt application bootstrap and shutdown
├── config/
│   ├── defaults.py             # Central tunable defaults
│   ├── models.py               # Typed settings and validation
│   └── store.py                # Per-machine/global persistence
├── controller/
│   ├── application.py          # Sole owner of live application/session state
│   ├── commands.py             # UI/hotkey intent objects
│   ├── snapshots.py            # Immutable state published to consumers
│   └── state_machine.py        # Valid states and transitions
├── scripts/
│   ├── model.py                # Blocks, tokens, paragraphs, sections, aliases
│   ├── parser.py               # Shared marker/escaping rules
│   ├── text_loader.py          # UTF-8 text loading
│   ├── docx_loader.py          # Read-only Word conversion
│   ├── legacy.py               # Old vamp conversion; discards resume cues
│   ├── reanchor.py             # Cursor preservation after reload
│   ├── watcher.py              # Debounced external-change notification
│   └── template.py             # New-script starter content
├── ui/
│   ├── overlay.py              # Frameless always-on-top presenter window
│   ├── controls.py             # Conventional control window
│   ├── script_view.py          # Token rendering and exact-word hit testing
│   ├── tray.py                 # Recovery and exit menu
│   ├── dev_tools.py            # Diagnostics/replay/settings surface
│   ├── first_run.py            # Setup, model download, calibration UI
│   ├── geometry.py             # DPI-aware placement and recovery
│   ├── scrolling.py            # Smooth/constant-speed scroll behavior
│   └── capture_exclusion.py    # Windows display-affinity adapter
├── audio/
│   ├── devices.py              # Enumeration and disconnect detection
│   ├── capture.py              # sounddevice stream lifecycle
│   ├── ring_buffer.py          # Preallocated 16 kHz mono buffer
│   └── levels.py               # Meter data derived outside callback
├── recognition/
│   ├── hardware.py             # CUDA, VRAM, compute-capability probing
│   ├── models.py               # Model inventory/download/verification
│   ├── calibration.py          # Candidate benchmarks and recommendation
│   ├── worker.py               # Single active Whisper job, latest-pending slot
│   ├── hypotheses.py           # Overlap deduplication/stable commitment
│   └── prompt_bias.py          # Upcoming-script bias construction
├── alignment/
│   ├── normalize.py            # Technical-term and pronunciation aliases
│   ├── matcher.py              # Bounded local fuzzy alignment
│   └── cursor.py               # Cursor, retakes, paragraphs, generations
├── input/
│   ├── hotkeys.py              # pynput listener and binding validation
│   └── overlay_actions.py      # Focused keyboard/mouse command mapping
├── diagnostics/
│   ├── events.py               # Structured event schema
│   ├── writer.py               # Nonblocking WAV/JSONL/metadata writer
│   ├── retention.py            # Count/size cleanup policy
│   ├── replay.py               # Recorded-input replay coordinator
│   └── clock.py                # Wall and virtual clock interfaces
├── platform/
│   ├── paths.py                # Windows storage locations
│   ├── startup.py              # Optional start-with-Windows integration
│   └── updates.py              # Check/notify/approval orchestration
└── resources/                  # Icons and packaged static data

tests/
├── unit/                       # Pure parsing, matching, state, and policy tests
├── integration/                # Component and thread-boundary tests
├── gui/                        # Qt interaction tests
├── replay/                     # Deterministic audio/event fixtures
├── fixtures/                   # Scripts, docx files, audio, hardware reports
└── manual/                     # Versioned Windows/Camtasia checklists
```

The directories describe boundaries, not permission to create future placeholders. Each milestone should add only modules needed by that milestone.

## 2. Major application components

1. **Application controller and state machine.** The single authority for loaded script, session mode (`IDLE`, `TRACKING`, `SOFT_HOLD`, `VAMPING`, `PAUSED`, `CONSTANT_SPEED`, `FINISHED`), cursor, take counts, click-through restoration, recognition generation, and orderly shutdown.
2. **Prompter Overlay.** A frameless, always-on-top, independently movable/resizable display with opaque text, adjustable background transparency, exact-word interaction, status banners, smooth scrolling, and optional click-through/capture exclusion.
3. **Control Window and system tray.** Normal-window controls for scripts, sessions, audio, modes, settings, calibration, diagnostics, and updates; closing it hides rather than exits. The overlay link, `Ctrl+Alt+O`, and tray must all recover the same instance.
4. **Script domain and workflow.** Read-only ingestion of UTF-8 `.txt` and `.docx`, typed block/token model, marker escaping, legacy vamp conversion, pronunciation aliases, recent files, starter creation, file watching, parse diagnostics, and cursor re-anchoring.
5. **Scrolling, navigation, and retakes.** Constant-speed operation, cursor-following animation, manual override, focused keys, word clicks, section/paragraph retakes, and per-section take counters.
6. **Audio pipeline.** Microphone selection, nonblocking callback, preallocated ring buffer, level data, disconnect handling, and explicit flushing at discontinuities.
7. **Whisper recognition and calibration.** Hardware probing, safe Pascal compute selection, model acquisition/verification, prerecorded and optional spoken calibration, overlapping-window transcription, latest-pending scheduling, prompt biasing, latency/backlog metrics, and stable hypothesis commitment.
8. **Deterministic alignment.** Canonical normalization plus aliases, bounded local scoring, stricter backward jumps, generation-aware commits, soft hold, and end-of-script detection. There is no LLM fallback.
9. **Manual vamp control.** `Ctrl+Alt+V` is the only entry/exit command. It freezes the cursor, stops recognition and diagnostic audio capture, preserves a silent replay interval, temporarily enables click-through, then restores the exact prior state.
10. **Diagnostics and replay.** Opt-in local WAV/JSONL/metadata capture outside vamp speech, bounded retention, immutable diagnostics snapshots, virtual-clock replay, model management, and tuning visibility. It does not expose or export a transcript.
11. **Windows integration and distribution.** DPI/monitor recovery, capture exclusion, global hotkeys, local settings, optional startup, update notification with approval gates, PyInstaller `--onedir`, and an installer/uninstaller.

## 3. Dependencies

### Runtime

- Python 3.11 or newer within the compatible ranges verified during packaging
- `PySide6`: windows, signals, animation, timers, settings UI, and system tray
- `faster-whisper`: offline speech recognition
- `sounddevice`: microphone enumeration and callback capture
- `numpy`: preallocated audio storage and signal data
- `rapidfuzz`: normalization support, bounded alignment, and reload re-anchoring
- `pynput`: configurable Windows global hotkeys
- `watchdog`: external script change detection
- `python-docx`: read-only `.docx` ingestion

### Development, test, and packaging

- `pytest` for unit and integration tests
- `pytest-qt` for Qt signals, timers, windows, and interaction tests
- A coverage tool such as `pytest-cov` for milestone regression visibility
- `PyInstaller` using `--onedir`
- Inno Setup or an equivalent Windows installer builder
- Formatting, linting, and type-checking tools should be selected once and pinned with the first implementation milestone; avoid adding tools without a CI or local quality-gate use.

### External/system requirements

- Windows 10 or Windows 11
- PortAudio support delivered through the selected `sounddevice` installation/package path
- Compatible NVIDIA driver/CUDA/cuDNN only when CUDA acceleration is selected; CPU operation remains mandatory
- Whisper model files downloaded during first-run setup, never bundled in the installer
- Camtasia is used only for manual capture-exclusion verification and is not an application dependency

There is deliberately no Ollama client, LLM runtime, cloud SDK, transcript/caption library, or audio-output dependency.

## 4. State ownership and thread boundaries

### Ownership

- The **Qt main thread** owns the application controller, authoritative session state, script model, state machine, cursor/take counts, alignment decisions, window instances, widget state, and scroll animation.
- Views receive immutable snapshots and emit commands. Neither window owns a duplicate session model.
- The controller owns a monotonically increasing **generation ID**. Retakes, direct cursor moves, reloads, pauses, vamp transitions, and model changes increment it and invalidate old audio, hypotheses, and recognition results.
- Configuration is changed through the controller/configuration service and published as validated immutable snapshots. Click-through is always reset to off on launch.

### Execution contexts

| Context | Owns/does | Must never do |
|---|---|---|
| Qt main thread | Widgets, controller, state transitions, alignment commits, scrolling, input routing | Block on audio, Whisper, model downloads, file I/O, or diagnostic writes |
| `sounddevice` callback | Copies frames into preallocated storage and returns | Allocate without bound, log, write files, transcribe, emit widget calls, or wait on locks |
| Recognition worker | Whisper model, window extraction, transcription, hypothesis updates, latency/backlog measurement | Touch widgets, mutate controller state directly, or accumulate an unbounded job queue |
| Diagnostic writer | WAV/JSONL/metadata persistence and flush | Block the audio callback/UI or store vamp speech |
| File watcher | Detect/debounce file changes and request reload | Parse into shared state or touch widgets directly |
| Hotkey listener | Detect validated global bindings and emit commands | Manipulate widgets or session state directly |
| Download/calibration jobs | Model transfer, verification, benchmarking | Freeze the UI or change active models without controller approval |

### Boundary rules

- Cross-thread messages use Qt signals, bounded queues, immutable values, and generation IDs.
- Recognition scheduling permits one active job and one replaceable pending window; the newest pending complete window wins.
- Diagnostic queues are bounded and surface dropped-event/backlog status rather than blocking producers.
- File changes are parsed into a candidate immutable model; the controller atomically adopts it only after successful parsing and re-anchoring.
- Hotkeys and watcher events become the same controller commands used by the GUI, avoiding divergent behavior.
- Shutdown order is controller stop request, audio stop, worker cancellation/drain, diagnostic flush, settings persistence, then window/process exit.

## 5. Milestone-by-milestone implementation plan

No milestone should add placeholder implementations for later milestones.

### Milestone 1: Domain foundation and text parser

- Align project metadata with Python 3.11+ and establish test/quality tooling.
- Add typed configuration, script blocks/tokens/paragraphs/sections, cursor anchors, and state enums.
- Implement `.txt` parsing for headings, notes, comments, vamp blocks, pronunciation aliases, escaping, paragraph boundaries, line-numbered errors, and legacy vamp conversion that ignores old resume cue lines.
- Define controller commands/snapshots and state-transition rules without building the GUI.

### Milestone 2: Two-window shell and lifecycle

- Build one Prompter Overlay, one Control Window, and one shared controller on the Qt main thread.
- Add independent geometry persistence, mixed-monitor/DPI-aware recovery, tray behavior, close-to-hide, clean exit, and `Ctrl+Alt+O` recovery.
- Ensure click-through starts off and opening controls does not change session state.

### Milestone 3: Overlay interaction and Windows behavior

- Add frameless/always-on-top behavior, drag/resize, background transparency, opaque script text, text size, focused controls, and adjustable appearance.
- Add click-through via control window and `Ctrl+Alt+C`, binding validation, and system-tray parity.
- Add capture exclusion as an off-by-default, checked Windows adapter that reports unsupported/failure states and reapplies after handle recreation.

### Milestone 4: Complete script workflow

- Add new `.txt` creation with starter template, default-editor opening, file dialogs, drag/drop, command-line opening, recent scripts, and last-script reopening.
- Add read-only `.docx` loading with heading/paragraph conversion and ignored tables/images/headers/footers.
- Add debounced watching, Word-lock retry, atomic hot reload, last-valid-model retention, detailed parse errors, and fuzzy cursor re-anchoring.

### Milestone 5: Constant-speed usable product

- Render headings, narration, notes, and vamp blocks with correct matchability and exact-word hit targets.
- Add smooth/clamped scrolling, constant-speed controls, temporary manual override, exact-word clicks, arrow navigation, section/paragraph retakes, and take counters.
- Add Control Window pause/resume, `PAUSED`, `FINISHED`, and behavior when no recognition model exists.
- This milestone must produce a useful teleprompter without microphone or Whisper setup.

### Milestone 6: Audio capture and diagnostic foundation

- Add device enumeration/selection, live level meter, 16 kHz mono callback capture, preallocated ring buffer, and disconnect-to-pause behavior.
- Add opt-in diagnostic consent, bounded asynchronous WAV/JSONL/metadata writing, retention by count and size, deletion controls, and generation/discontinuity events.
- Ensure diagnostic recording is disabled by default and never creates transcript export artifacts.

### Milestone 7: Hardware detection, model setup, and calibration

- Probe CUDA, VRAM, and compute capability; enforce `int8_float32` for Pascal and safe CPU fallback.
- Add resumable model download, verification, storage selection, installed-model management, and active-model deletion protection.
- Benchmark prerecorded calibration audio, optionally support explicit spoken calibration, recommend a model, explain fallbacks, and persist user overrides.

### Milestone 8: Offline voice tracking and alignment

- Add overlapping Whisper windows with VAD, greedy decoding, no previous-text conditioning, next-script prompt bias, and one-active/latest-pending scheduling.
- Implement stable hypothesis commitment and fuzzy overlap deduplication.
- Add technical normalization/default aliases/script-local overrides and bounded local alignment with backward threshold, misses, soft hold, and generation-aware result rejection.
- Connect confident commits to cursor/scroll and automatic end-of-script behavior; degrade visibly to constant speed on unavailable/slow recognition.

### Milestone 9: Manual vamp workflow

- Implement manual entry/exit exclusively through `Ctrl+Alt+V`, with disabled behavior while normally paused and ignored retake commands while vamping.
- Freeze script/cursor, stop recognition, flush stale audio, pause diagnostic WAV storage, log silent replay duration, show deterministic VAMP ON/OFF messages, and restore prior click-through exactly.
- Support planned/unplanned and final vamp behavior. Never inspect speech for a resume condition.

### Milestone 10: Dev Tools and deterministic replay

- Add diagnostics, effective configuration, hardware/audio/model/queue/alignment views, safe live tuning, calibration rerun, model management, and diagnostic storage controls inside the Control Window.
- Add real-time and accelerated replay using a virtual clock for timeouts, scrolling, debounce, vamp intervals, and event timestamps.
- Record enough versions/configuration metadata to explain cross-machine differences without exporting recognized transcript text as a user feature.

### Milestone 11: Installer, first-run completion, and updates

- Build and smoke-test PyInstaller `--onedir`, installer/uninstaller, shortcuts, optional startup behavior, and clean removal while respecting user diagnostic/model-data choices.
- Finish first-run microphone/model/constant-speed paths.
- Add update checks that can be disabled, show release notes, require separate download/install approval, and never update during an active session.
- Run the complete version 1 acceptance matrix and document supported hardware/package combinations.

## 6. Automated and manual tests for each milestone

### Milestone 1 tests

**Automated:** table-driven parser tests for every marker and escape; paragraph/line mapping; comments and aliases excluded from narration; legacy vamp conversion with both old resume syntaxes ignored; exact error locations; immutable models; allowed/forbidden state transitions; configuration validation.

**Manual:** review starter syntax and parser errors against representative tutorial scripts. Confirm no LLM, spoken-cue, or transcript-export concepts appear in runtime dependencies or domain APIs.

### Milestone 2 tests

**Automated:** Qt tests for singleton windows, shared snapshots, close-to-hide, restore-without-state-change, tray commands, clean shutdown signaling, separate geometry records, and off-screen recovery calculations.

**Manual:** Windows 10/11 launch; move/resize both windows independently; mixed DPI at 100/125/150%; disconnect/reconnect a monitor; verify both windows remain reachable and click-through starts off.

### Milestone 3 tests

**Automated:** hotkey validation for duplicates/incomplete/unsupported chords; command routing through signals; click-through state transitions; opacity changes leave text style opaque; mocked capture-exclusion success/failure/unsupported/handle-recreation paths.

**Manual:** drag/resize and focused keys; recover controls while click-through; test actual global hotkeys with VS Code/PowerPoint focused; run the Camtasia full-screen/region/multi-monitor capture-exclusion matrix and confirm failure fallback.

### Milestone 4 tests

**Automated:** `.txt` encoding and `.docx` fixture conversion; ignored Word content; recent/last-file policy; debounce/coalescing; locked-file retry; parse failure retains prior model; re-anchor within section/paragraph, preceding-heading fallback, start fallback, and vamp-preserving reload.

**Manual:** create a script and verify default editor launch; edit/save repeatedly from Notepad, VS Code, and Word; test temporary Word locks; drag/drop and command-line open; inspect actionable error messages and Open in Editor behavior.

### Milestone 5 tests

**Automated:** rendering roles and nonmatchable blocks; scroll target/easing/velocity limits; manual-override timer with injectable clock; word hit testing; retake increment rules; paragraph/section fallback; arrow navigation not incrementing takes; pause/finish/constant-speed transitions.

**Manual:** complete a full script in constant-speed mode without a model; adjust rate/text size; click exact words; retake before/after headings; verify visual readability over common recording applications and that no app sound is produced.

### Milestone 6 tests

**Automated:** ring-buffer wraparound and capacity; callback bounded-work contract where practical; device-loss transition; queue saturation behavior; WAV format/length; JSONL schema; retention at 20 sessions/5 GB boundaries; generation flushing; diagnostics-off creates no session data.

**Manual:** enumerate and switch real microphones; inspect levels; unplug the active device and verify pause/no silent switch; run a long capture while watching UI responsiveness, memory, drops, and clean shutdown flush.

### Milestone 7 tests

**Automated:** fixture-driven CPU/CUDA/VRAM/compute-capability selection, including GTX 1060 3 GB/6 GB and Pascal float16 rejection; download resume/checksum/failure; storage migration policy; calibration ranking; override persistence; active-model deletion refusal.

**Manual:** run setup on the home CPU machine and lab GTX 1060; inspect effective device/model/compute type; interrupt/retry downloads; test low disk and bad CUDA paths; verify constant-speed remains available throughout.

### Milestone 8 tests

**Automated:** one-active/latest-pending scheduling; stale-generation rejection; overlap deduplication with slightly different Whisper words; pause boundaries; prompt-bias window movement; default and local aliases including `Verse Code` to `VS Code`; bounded/repeated-phrase alignment; backward threshold; soft-hold entry/recovery/timeout; end detection.

**Manual:** read technical scripts on both target machines; measure latency/backlog and cursor stability; pause/restart/repeat phrases; force recognition loss; verify soft hold and fallback; confirm no network traffic or Ollama process is required.

### Milestone 9 tests

**Automated:** valid vamp transitions; `Ctrl+Alt+V` as sole toggle; ignored commands while paused/vamping; planned/unplanned reminder choice; cursor freeze; generation/audio flush; exact click-through restoration; diagnostic gaps represented as silence with no vamp frames; final vamp to finished.

**Manual:** perform scripted-to-live-demo-to-script workflows while using VS Code/browser/PowerPoint; speak arbitrary words and old resume phrases during vamp and verify nothing resumes; inspect diagnostic artifacts to confirm vamp speech was not stored.

### Milestone 10 tests

**Automated:** diagnostics snapshot consistency; safe tuning validation; virtual-clock determinism at real-time/accelerated rates; replayed timeout/debounce/scroll/vamp events; storage deletion; version/config difference reporting; no transcript export command or artifact.

**Manual:** replay the same session repeatedly and compare event/cursor outcomes; replay across target machines and inspect disclosed differences; exercise model/storage controls; confirm Dev Tools remains part of the Control Window rather than a third primary window.

### Milestone 11 tests

**Automated:** clean-environment packaged launch smoke test; resource/dependency inclusion; settings migration; updater state/approval tests; active-session update prohibition; uninstall policy tests where automation is reliable.

**Manual:** install, upgrade, and uninstall on clean Windows 10/11 systems; first run with/without CUDA, microphone, network, and model; Start Menu/optional desktop/startup shortcuts; cancellation at every update gate; full acceptance test and Camtasia checklist.

## 7. Risks or contradictions found in the specification

1. **Older and current specifications conflict.** `README_FABLE.md` describes Ollama, semantic rescue, transcript correction/export, and spoken/semantic resume cues. The revised `README_Codex_Improvements(1).md` explicitly removes them. This plan treats the revised document as authoritative and retains legacy resume lines only as ignored conversion input.
2. **Repository metadata currently conflicts with the specification.** `pyproject.toml` allows Python 3.10 and contains no runtime dependencies, while the current specification requires Python 3.11+ and names the runtime stack. Correct this only when implementation begins; this planning task does not modify it.
3. **The repository-local README files are incomplete.** `README.md` is only a starter description and `README_Codex_Improvements.md` does not contain the actual revised specification, which lives one directory above under a suffixed filename. That creates a high risk that future agents follow the wrong document. Consolidation should be an explicit documentation task before implementation, without reviving removed features.
4. **State diagram omissions.** The diagram does not show all plausible transitions, such as `PAUSED` or `VAMPING` from constant-speed mode, returning from `PAUSED` to the previously selected mode, ending a session early, or changing scripts. Milestone 1 must turn prose into an explicit transition table and flag any product choice that cannot be inferred safely.
5. **Pause wording is inconsistent.** `PAUSED` says recognition is stopped, while degradation behavior says a microphone disconnect should “pause”; the expected resume target and whether constant-speed operation is affected need explicit controller semantics.
6. **Vamp markers do not auto-stop.** The spec calls them manual stops in constant-speed mode but also says reaching a marker never automatically activates vamp mode. The likely interpretation is that the user must press `Ctrl+Alt+V`; testing should verify scrolling behavior at a visible marker, and product clarification is needed on whether constant-speed scrolling itself pauses at the marker.
7. **Diagnostic content versus no transcript export.** Diagnostics require JSONL recognition/alignment events and replay, while transcript export is prohibited. Diagnostic schemas must minimize/clearly classify recognized text, remain opt-in and development-oriented, and provide no transcript-export UI. The exact amount of transcript text required for useful replay needs a privacy/product decision.
8. **Finished “session summary” is underspecified.** It explicitly includes take counts and forbids transcript export, but does not define other summary fields or retention. Version 1 should keep it minimal unless specified.
9. **Update delivery is underspecified.** The source of version metadata, release notes, download packages, signature verification, rollback, and trust model are not defined. Do not invent an insecure updater; resolve these before Milestone 11.
10. **CUDA compatibility guidance can age.** Driver, CUDA, cuDNN, CTranslate2, and faster-whisper compatibility must be pinned and verified against both target machines during packaging. Calibration must decide actual usable configurations rather than relying on theoretical VRAM tables.
11. **Capture exclusion is recorder-dependent.** `WDA_EXCLUDEFROMCAPTURE` is not a security boundary and may behave differently with Camtasia capture modes. It remains off by default and requires the real manual matrix.
12. **Audio callback “lock-free” expectations need care in Python.** The required bounded, preallocated, nonblocking behavior is clear, but true lock-free guarantees depend on the selected ring-buffer implementation and callback/library behavior. Measure callback timing and drops rather than claiming an unverified guarantee.
13. **Replay determinism has limits.** Recognition may differ across model versions, hardware, and compute types. Determinism applies to the recorded clock/events and a pinned environment; cross-machine differences must be visible, not hidden.
14. **`.docx` watch semantics are less defined than `.txt`.** `watchdog` is named for text, while Word uses temporary/replace saves and locks. The implementation needs debounce, retry, and atomic-adoption tests against actual Word behavior.
15. **Hotkey conflicts cannot be fully predicted.** Validation can prevent internal duplicates and malformed chords, but OS/application conflicts must be detected at registration where possible and explained with a rebind path.

## Version 1 scope gate

Before accepting any milestone, verify that it does not introduce cloud calls, Ollama/LLM dependencies, semantic rescue, transcript correction/export, caption workflows, automatic or spoken vamp cues, audio output, web/mobile support, rich text editing, or product-level recording. Diagnostic audio/replay is the sole narrowly defined local recording exception and remains disabled by default.
