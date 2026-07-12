"""Display/navigation projection of the parsed script model."""

from dataclasses import dataclass
import re

from .model import Paragraph, PresenterNote, Script, SectionHeading, VampBlock


_WORD_RE = re.compile(r"\S+")


@dataclass(frozen=True, slots=True)
class DisplayWord:
    text: str
    index: int
    paragraph_index: int
    section_index: int


@dataclass(frozen=True, slots=True)
class DisplayBlock:
    kind: str
    text: str
    words: tuple[DisplayWord, ...] = ()
    section_index: int = 0


@dataclass(frozen=True, slots=True)
class ScriptPresentation:
    blocks: tuple[DisplayBlock, ...]
    words: tuple[DisplayWord, ...]
    paragraph_starts: tuple[int, ...]
    section_count: int

    def section_at(self, cursor: int) -> int:
        if not self.words:
            return 0
        return self.words[min(max(cursor, 0), len(self.words) - 1)].section_index

    def previous_line(self, cursor: int) -> int:
        starts = [start for start in self.paragraph_starts if start < cursor]
        return starts[-1] if starts else 0

    def next_line(self, cursor: int) -> int:
        return next((start for start in self.paragraph_starts if start > cursor), self.last_word)

    @property
    def last_word(self) -> int:
        return max(0, len(self.words) - 1)


def build_presentation(script: Script) -> ScriptPresentation:
    blocks: list[DisplayBlock] = []
    words: list[DisplayWord] = []
    paragraph_starts: list[int] = []
    section_index = 0
    section_count = 1
    paragraph_index = 0

    for block in script.blocks:
        if isinstance(block, SectionHeading):
            if blocks:
                section_index += 1
            section_count = max(section_count, section_index + 1)
            blocks.append(DisplayBlock("heading", block.text, section_index=section_index))
        elif isinstance(block, Paragraph):
            paragraph_words: list[DisplayWord] = []
            for match in _WORD_RE.finditer(block.text):
                word = DisplayWord(match.group(), len(words), paragraph_index, section_index)
                words.append(word)
                paragraph_words.append(word)
            if paragraph_words:
                paragraph_starts.append(paragraph_words[0].index)
            blocks.append(
                DisplayBlock("paragraph", block.text, tuple(paragraph_words), section_index)
            )
            paragraph_index += 1
        elif isinstance(block, PresenterNote):
            blocks.append(DisplayBlock("note", block.text, section_index=section_index))
        elif isinstance(block, VampBlock):
            blocks.append(
                DisplayBlock("vamp", block.reminder or "Unscripted demonstration", section_index=section_index)
            )

    return ScriptPresentation(
        tuple(blocks), tuple(words), tuple(paragraph_starts), section_count
    )
