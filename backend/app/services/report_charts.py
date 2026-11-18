"""Charts for written reports, drawn with Pillow as PNGs that both the Word and PDF files embed.

Only aggregate figures go in: totals by week, category, household size and donor or grant.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 640  # drawn large so it stays sharp when scaled to page width
INK, MUTED, GRID, BAR = (15, 27, 51), (90, 100, 120), (222, 227, 237), (32, 95, 197)
MAX_BARS = 12


@dataclass(frozen=True)
class Chart:
    title: str
    alt: str  # a text version of the chart, for screen readers and as the figure caption
    png: bytes
    width: int = WIDTH
    height: int = HEIGHT


def _font(size: int):
    return ImageFont.load_default(size=size)


def _fit(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    while len(text) > 1 and draw.textlength(text, font=font) > max_width:
        text = text[:-2] + "…"
    return text


def bar_chart(title: str, items: list[tuple[str, float]], *, horizontal: bool = False) -> bytes:
    items = items[:MAX_BARS]
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 28), title, fill=INK, font=_font(38))
    big, small = _font(28), _font(24)
    top = max(value for _, value in items) or 1
    left, right, head, foot = 40, WIDTH - 40, 110, HEIGHT - 40
    if horizontal:
        label_w = 260
        row = (foot - head) / len(items)
        for i, (label, value) in enumerate(items):
            y = head + i * row
            draw.text(
                (left, y + row / 2),
                _fit(draw, label, small, label_w - 20),
                fill=INK,
                font=small,
                anchor="lm",
            )
            length = (right - left - label_w - 110) * value / top
            draw.rectangle(
                [left + label_w, y + row * 0.2, left + label_w + length, y + row * 0.8], fill=BAR
            )
            draw.text(
                (left + label_w + length + 12, y + row / 2),
                f"{value:g}",
                fill=INK,
                font=big,
                anchor="lm",
            )
    else:
        base = foot - 50
        draw.line([left, base, right, base], fill=GRID, width=3)
        slot = (right - left) / len(items)
        for i, (label, value) in enumerate(items):
            x = left + i * slot
            height = (base - head - 40) * value / top
            draw.rectangle([x + slot * 0.18, base - height, x + slot * 0.82, base], fill=BAR)
            draw.text(
                (x + slot / 2, base - height - 8), f"{value:g}", fill=INK, font=big, anchor="ms"
            )
            draw.text(
                (x + slot / 2, base + 12),
                _fit(draw, label, small, int(slot)),
                fill=MUTED,
                font=small,
                anchor="mt",
            )
    out = BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


def _chart(title: str, items: list[tuple[str, float]], horizontal: bool = False) -> Chart | None:
    items = [(label, value) for label, value in items if value]
    if not items:
        return None  # nothing to plot: leave the chart out rather than draw an empty frame
    alt = f"{title}: " + ", ".join(f"{label} {value:g}" for label, value in items[:MAX_BARS])
    return Chart(title, alt, bar_chart(title, items, horizontal=horizontal))


def charts_for(preset: str, summary: dict[str, Any], weekly: list[dict[str, Any]]) -> list[Chart]:
    """The visuals for a report, in reading order; charts with no data are skipped."""
    by_owner = {"donor": ("Items by donor", "by_donor"), "grant": ("Items by grant", "by_grant")}
    charts = [
        _chart(
            "Items distributed per week",
            [(f"{w['week']:%b %d}", w["items"]) for w in weekly[-MAX_BARS:]],
        ),
        _chart(
            "Most distributed categories",
            [(c["category"], c["items"]) for c in summary["top_categories"]],
            True,
        ),
        _chart("Households by size", list(summary["household_sizes"].items())),
    ]
    if preset in by_owner:
        title, key = by_owner[preset]
        charts.append(_chart(title, [(row["label"], row["items"]) for row in summary[key]], True))
    return [chart for chart in charts if chart]
