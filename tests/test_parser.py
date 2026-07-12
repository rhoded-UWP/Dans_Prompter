from pathlib import Path

import pytest

from dans_teleprompter.scripts import (
    Paragraph,
    PresenterNote,
    ScriptParseError,
    SectionHeading,
    VampBlock,
    parse_text,
)


def test_parses_section_headings_and_paragraphs() -> None:
    script = parse_text("## Introduction\n\nFirst line.\nSecond line.\n\nNext paragraph.", "talk.txt")

    assert script.source == Path("talk.txt")
    assert script.blocks == (
        SectionHeading("Introduction", 1),
        Paragraph("First line.\nSecond line.", 3, 4),
        Paragraph("Next paragraph.", 6, 6),
    )


def test_parses_plain_vamp_marker() -> None:
    script = parse_text("Before.\n<<VAMP>>\nAfter.")

    assert script.blocks == (
        Paragraph("Before.", 1, 1),
        VampBlock(None, 2),
        Paragraph("After.", 3, 3),
    )


def test_parses_vamp_marker_with_reminder() -> None:
    script = parse_text("<<VAMP: Live-code the route handler>>")

    assert script.blocks == (VampBlock("Live-code the route handler", 1),)


def test_converts_legacy_vamp_and_ignores_resume_cues() -> None:
    script = parse_text(
        "@@ VAMP: Live-code the route handler\n"
        ">> resume: back to the slides\n"
        ">> resume-when: I signal the return\n"
        "Continue here."
    )

    assert script.blocks == (
        VampBlock("Live-code the route handler", 1, converted_from_legacy=True),
        Paragraph("Continue here.", 4, 4),
    )


def test_collects_pronunciation_aliases_outside_display_blocks() -> None:
    script = parse_text("@@ PRONOUNCE: VS Code = V S Code\nSay VS Code.")

    assert [(alias.canonical, alias.spoken, alias.line_number) for alias in script.pronunciation_aliases] == [
        ("VS Code", "V S Code", 1)
    ]
    assert script.blocks == (Paragraph("Say VS Code.", 2, 2),)


def test_parses_presenter_notes_as_non_narration_blocks() -> None:
    script = parse_text("Narration.\n-- Take a breath\nMore narration.")

    assert script.blocks == (
        Paragraph("Narration.", 1, 1),
        PresenterNote("Take a breath", 2),
        Paragraph("More narration.", 3, 3),
    )


def test_hidden_comments_are_omitted_and_split_paragraphs() -> None:
    script = parse_text("First.\n// Never display this.\nSecond.")

    assert script.blocks == (Paragraph("First.", 1, 1), Paragraph("Second.", 3, 3))


@pytest.mark.parametrize(
    ("source_line", "expected"),
    [
        (r"\## spoken heading", "## spoken heading"),
        (r"\-- spoken note", "-- spoken note"),
        (r"\// spoken comment", "// spoken comment"),
        (r"\<<VAMP>> spoken marker", "<<VAMP>> spoken marker"),
        (r"\@@ PRONOUNCE: spoken", "@@ PRONOUNCE: spoken"),
        (r"\@@ VAMP: spoken", "@@ VAMP: spoken"),
        (r"\>> resume: spoken", ">> resume: spoken"),
    ],
)
def test_backslash_escapes_each_marker_family(source_line: str, expected: str) -> None:
    script = parse_text(source_line)

    assert script.blocks == (Paragraph(expected, 1, 1),)


@pytest.mark.parametrize(
    ("source_line", "message_fragment"),
    [
        ("##", "section heading is empty"),
        ("--", "presenter note is empty"),
        ("<<VAMP", "Malformed vamp marker"),
        ("<<VAMP: >>", "reminder cannot be empty"),
        ("@@ VAMP reminder", "Malformed legacy vamp marker"),
        ("@@ VAMP:", "legacy vamp reminder cannot be empty"),
        ("@@ PRONOUNCE term = words", "Malformed pronunciation marker"),
        ("@@ PRONOUNCE: term", "exactly one '='"),
        ("@@ PRONOUNCE: = words", "Both sides"),
        ("@@ PRONOUNCE: term =", "Both sides"),
        ("@@ UNKNOWN: value", "Unknown or malformed script marker"),
    ],
)
def test_malformed_markers_raise_useful_line_numbered_errors(
    source_line: str, message_fragment: str
) -> None:
    with pytest.raises(ScriptParseError) as raised:
        parse_text(f"Valid narration.\n{source_line}\nLater narration.", "lesson.txt")

    error = raised.value
    assert error.source == Path("lesson.txt")
    assert error.line_number == 2
    assert error.line_text == source_line
    assert message_fragment in error.explanation
    assert "lesson.txt:2:" in str(error)
    assert source_line in str(error)


def test_unrecognized_backslash_is_preserved_as_narration() -> None:
    script = parse_text(r"\ordinary path")

    assert script.blocks == (Paragraph(r"\ordinary path", 1, 1),)


def test_empty_input_produces_empty_script() -> None:
    script = parse_text("", "empty.txt")

    assert script.blocks == ()
    assert script.pronunciation_aliases == ()
