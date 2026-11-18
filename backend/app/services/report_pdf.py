"""PDF version of a written report: same content and charts as the Word file, built with fpdf2."""

from __future__ import annotations

from io import BytesIO

from fpdf import FPDF

MARGIN = 18
PAGE_WIDTH = 210  # A4, mm
IMAGE_WIDTH = PAGE_WIDTH - 2 * MARGIN
# The built-in PDF fonts are Latin-1 only; swap the typographic characters an AI draft likes to use.
PLAIN = str.maketrans(
    {"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-", "…": "...", "•": "-"}
)


def _latin(text: str) -> str:
    return text.translate(PLAIN).encode("latin-1", "replace").decode("latin-1")


def build_report_pdf(content, charts) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    pdf.set_auto_page_break(auto=True, margin=MARGIN)
    pdf.set_title(_latin(content.title))
    pdf.add_page()

    def write(text: str, style: str = "", size: int = 11, after: float = 3) -> None:
        pdf.set_font("Helvetica", style, size)
        pdf.multi_cell(0, size * 0.5, _latin(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(after)

    write(content.title, "B", 20, 4)
    if content.note:
        write(content.note, "I", 9)
    for paragraph in content.story:
        write(paragraph)
    for chart in charts:
        height = IMAGE_WIDTH * chart.height / chart.width
        if pdf.get_y() + height > pdf.page_break_trigger:
            pdf.add_page()
        pdf.image(BytesIO(chart.png), x=MARGIN, w=IMAGE_WIDTH, alt_text=_latin(chart.alt))
        pdf.ln(4)
    write("Figures", "B", 14, 2)
    for line in content.figures:
        write(line, after=1)
    return bytes(pdf.output())
