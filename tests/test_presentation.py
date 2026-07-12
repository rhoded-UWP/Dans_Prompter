from pathlib import Path

from dans_teleprompter.scripts import parse_text
from dans_teleprompter.scripts.presentation import build_presentation


def test_builds_words_sections_and_paragraph_navigation() -> None:
    script = parse_text(
        "## Opening\nOne two.\n\nThree four.\n## Close\nFive.", Path("talk.txt")
    )

    presentation = build_presentation(script)

    assert [word.text for word in presentation.words] == ["One", "two.", "Three", "four.", "Five."]
    assert presentation.paragraph_starts == (0, 2, 4)
    assert presentation.section_count == 2
    assert presentation.section_at(4) == 1
    assert presentation.previous_line(3) == 2
    assert presentation.next_line(2) == 4


def test_preserves_notes_and_vamp_blocks_as_non_spoken_display_blocks() -> None:
    presentation = build_presentation(
        parse_text("Words.\n-- Breathe\n<<VAMP: Show the demo>>")
    )

    assert [(block.kind, block.text) for block in presentation.blocks] == [
        ("paragraph", "Words."),
        ("note", "Breathe"),
        ("vamp", "Show the demo"),
    ]
    assert len(presentation.words) == 1
