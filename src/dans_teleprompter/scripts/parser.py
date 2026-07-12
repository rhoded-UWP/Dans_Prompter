"""Parser for Dan's Teleprompter plain-text script format."""

from dataclasses import dataclass
from pathlib import Path
import re

from .model import (
    Paragraph,
    PresenterNote,
    PronunciationAlias,
    Script,
    ScriptBlock,
    SectionHeading,
    VampBlock,
)


_VAMP_RE = re.compile(r"^<<VAMP(?::\s*(.*?))?>>$")
_PRONOUNCE_PREFIX = "@@ PRONOUNCE"
_LEGACY_VAMP_PREFIX = "@@ VAMP"
_ESCAPABLE_PREFIXES = ("##", "--", "//", "<<VAMP", "@@ PRONOUNCE", "@@ VAMP", ">> resume")


@dataclass(frozen=True, slots=True)
class ScriptParseError(ValueError):
    """A source-located error suitable for presentation to a user."""

    source: Path
    line_number: int
    line_text: str
    explanation: str

    def __str__(self) -> str:
        return (
            f"{self.source}:{self.line_number}: {self.explanation}\n"
            f"    {self.line_text}"
        )


def parse_text(text: str, source: str | Path = "<memory>") -> Script:
    """Parse UTF-8-decoded plain text into an immutable :class:`Script`.

    The caller is responsible for decoding file bytes. Newline styles are
    normalized by ``splitlines`` and source line numbers are one-based.
    """

    source_path = Path(source)
    blocks: list[ScriptBlock] = []
    aliases: list[PronunciationAlias] = []
    paragraph_lines: list[tuple[int, str]] = []

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        blocks.append(
            Paragraph(
                text="\n".join(line for _, line in paragraph_lines),
                start_line=paragraph_lines[0][0],
                end_line=paragraph_lines[-1][0],
            )
        )
        paragraph_lines.clear()

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.rstrip()

        if not line.strip():
            flush_paragraph()
            continue

        escaped = _unescape_marker(line)
        if escaped is not None:
            paragraph_lines.append((line_number, escaped))
            continue

        if line.startswith("//"):
            flush_paragraph()
            continue

        if line.startswith("##"):
            flush_paragraph()
            heading = _required_payload(line, "##", source_path, line_number, "section heading")
            blocks.append(SectionHeading(heading, line_number))
            continue

        if line.startswith("--"):
            flush_paragraph()
            note = _required_payload(line, "--", source_path, line_number, "presenter note")
            blocks.append(PresenterNote(note, line_number))
            continue

        if line.startswith("<<VAMP"):
            flush_paragraph()
            match = _VAMP_RE.fullmatch(line)
            if match is None:
                _fail(source_path, line_number, line, "Malformed vamp marker; use '<<VAMP>>' or '<<VAMP: reminder>>'.")
            reminder = match.group(1)
            if reminder is not None:
                reminder = reminder.strip()
                if not reminder:
                    _fail(source_path, line_number, line, "A vamp reminder cannot be empty; use '<<VAMP>>' for no reminder.")
            blocks.append(VampBlock(reminder, line_number))
            continue

        if line.startswith(_PRONOUNCE_PREFIX):
            flush_paragraph()
            aliases.append(_parse_pronunciation(line, source_path, line_number))
            continue

        if line.startswith(_LEGACY_VAMP_PREFIX):
            flush_paragraph()
            reminder = _parse_legacy_vamp(line, source_path, line_number)
            blocks.append(VampBlock(reminder, line_number, converted_from_legacy=True))
            continue

        if line.startswith(">> resume:") or line.startswith(">> resume-when:"):
            flush_paragraph()
            continue

        if line.startswith("@@") or line.startswith(">> resume") or line.startswith("<<"):
            flush_paragraph()
            _fail(source_path, line_number, line, "Unknown or malformed script marker. Escape it with a leading backslash to speak it as narration.")

        paragraph_lines.append((line_number, line))

    flush_paragraph()
    return Script(source_path, tuple(blocks), tuple(aliases))


def _unescape_marker(line: str) -> str | None:
    if not line.startswith("\\"):
        return None
    candidate = line[1:]
    if candidate.startswith(_ESCAPABLE_PREFIXES):
        return candidate
    return None


def _required_payload(
    line: str,
    prefix: str,
    source: Path,
    line_number: int,
    label: str,
) -> str:
    payload = line[len(prefix) :].strip()
    if not payload:
        _fail(source, line_number, line, f"The {label} is empty; add text after '{prefix}'.")
    return payload


def _parse_pronunciation(line: str, source: Path, line_number: int) -> PronunciationAlias:
    suffix = line[len(_PRONOUNCE_PREFIX) :]
    if not suffix.startswith(":"):
        _fail(source, line_number, line, "Malformed pronunciation marker; use '@@ PRONOUNCE: term = spoken form'.")
    assignment = suffix[1:].strip()
    if assignment.count("=") != 1:
        _fail(source, line_number, line, "A pronunciation marker must contain exactly one '=' between the term and spoken form.")
    canonical, spoken = (part.strip() for part in assignment.split("=", 1))
    if not canonical or not spoken:
        _fail(source, line_number, line, "Both sides of a pronunciation alias must contain text.")
    return PronunciationAlias(canonical, spoken, line_number)


def _parse_legacy_vamp(line: str, source: Path, line_number: int) -> str:
    suffix = line[len(_LEGACY_VAMP_PREFIX) :]
    if not suffix.startswith(":"):
        _fail(source, line_number, line, "Malformed legacy vamp marker; use '@@ VAMP: reminder'.")
    reminder = suffix[1:].strip()
    if not reminder:
        _fail(source, line_number, line, "A legacy vamp reminder cannot be empty; use '<<VAMP>>' for no reminder.")
    return reminder


def _fail(source: Path, line_number: int, line_text: str, explanation: str) -> None:
    raise ScriptParseError(source, line_number, line_text, explanation)

