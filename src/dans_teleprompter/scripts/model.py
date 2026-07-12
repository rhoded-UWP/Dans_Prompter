"""Immutable domain objects produced by script parsing."""

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class Paragraph:
    """One narration paragraph, possibly spanning several source lines."""

    text: str
    start_line: int
    end_line: int


@dataclass(frozen=True, slots=True)
class SectionHeading:
    """A non-spoken section and retake anchor."""

    text: str
    line_number: int


@dataclass(frozen=True, slots=True)
class PresenterNote:
    """Visible, non-spoken direction for the presenter."""

    text: str
    line_number: int


@dataclass(frozen=True, slots=True)
class VampBlock:
    """A manual vamp marker with an optional presenter reminder."""

    reminder: str | None
    line_number: int
    converted_from_legacy: bool = False


@dataclass(frozen=True, slots=True)
class PronunciationAlias:
    """A canonical script term and one way it may be spoken."""

    canonical: str
    spoken: str
    line_number: int


ScriptBlock: TypeAlias = Paragraph | SectionHeading | PresenterNote | VampBlock


@dataclass(frozen=True, slots=True)
class Script:
    """A parsed script and its non-display pronunciation metadata."""

    source: Path
    blocks: tuple[ScriptBlock, ...]
    pronunciation_aliases: tuple[PronunciationAlias, ...] = ()

