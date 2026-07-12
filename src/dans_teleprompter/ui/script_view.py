"""Rich, exact-word-clickable script rendering surface."""

from html import escape

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QTextBrowser

from ..controller.state import TeleprompterState
from ..scripts.presentation import ScriptPresentation


class ScriptView(QTextBrowser):
    word_clicked = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("scriptView")
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.setFrameShape(QTextBrowser.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QTextBrowser { background: transparent; border: 0; }")
        palette = self.palette()
        palette.setColor(QPalette.Base, palette.color(QPalette.Window))
        self.setPalette(palette)
        self.anchorClicked.connect(self._anchor_clicked)

    def render(self, presentation: ScriptPresentation | None, state: TeleprompterState) -> None:
        if presentation is None:
            self.setHtml(self._empty_html(state.text_size))
            return

        body: list[str] = []
        for block in presentation.blocks:
            if block.kind == "heading":
                take = state.take_counts[min(block.section_index, len(state.take_counts) - 1)]
                body.append(
                    f'<p style="margin:30px 0 10px;color:#d6aa68;font-size:{state.text_size * 0.68:.0f}px;'
                    f'font-weight:600;letter-spacing:1px">{escape(block.text.upper())}'
                    f'<span style="color:#7b8089;font-size:{state.text_size * 0.42:.0f}px"> &nbsp; TAKE {take}</span></p>'
                )
            elif block.kind == "note":
                body.append(
                    f'<p style="margin:10px 0;color:#87909b;font-size:{state.text_size * 0.58:.0f}px;'
                    f'font-style:italic">◇ {escape(block.text)}</p>'
                )
            elif block.kind == "vamp":
                body.append(
                    f'<table width="100%" cellspacing="0" cellpadding="14" style="margin:20px 0">'
                    f'<tr><td bgcolor="#3d3023"><span style="color:#f3c47f;font-size:{state.text_size * 0.58:.0f}px;'
                    f'font-weight:700">VAMP OFF</span><br><span style="color:#e9e2d8;font-size:{state.text_size * 0.48:.0f}px">'
                    f'{escape(block.text)} · Ctrl+Alt+V will be added in the vamp milestone</span></td></tr></table>'
                )
            elif block.kind == "paragraph":
                rendered_words = " ".join(self._word_html(word.text, word.index, state) for word in block.words)
                body.append(f'<p style="margin:12px 0 24px;line-height:135%">{rendered_words}</p>')

        self.setHtml(self._document("".join(body), state.text_size))
        self.scrollToAnchor(f"word-{state.cursor_word}")

    def _word_html(self, text: str, index: int, state: TeleprompterState) -> str:
        if index < state.cursor_word:
            color, background, weight = "#626871", "transparent", "400"
        elif index == state.cursor_word:
            color, background, weight = "#17191d", "#f2b866", "700"
        else:
            color, background, weight = "#f5f1e9", "transparent", "500"
        return (
            f'<a name="word-{index}" href="word:{index}" style="text-decoration:none;color:{color};'
            f'background-color:{background};font-weight:{weight}">{escape(text)}</a>'
        )

    def _document(self, body: str, size: int) -> str:
        return (
            '<html><body style="margin:24px;color:#f5f1e9;font-family:Georgia,serif;'
            f'font-size:{size}px">{body}</body></html>'
        )

    def _empty_html(self, size: int) -> str:
        return self._document(
            f'<p style="color:#838994;text-align:center;font-size:{size * 0.7:.0f}px">'
            'OPEN A .TXT SCRIPT FROM CONTROLS<br><span style="font-size:70%">Your reading surface will appear here.</span></p>',
            size,
        )

    def _anchor_clicked(self, url: QUrl) -> None:
        if url.scheme() == "word":
            try:
                self.word_clicked.emit(int(url.path()))
            except ValueError:
                return
