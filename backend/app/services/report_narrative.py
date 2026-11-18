"""Written donor, grant and general reports: an AI draft from aggregate figures, or a template.

The AI only ever sees the aggregate summary (no rows, no participant codes). One short Groq call
with a hard timeout keeps the page quick; any failure falls back to the template, never an error.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx

from app.ai.provider import GPT_OSS_PREFIX, GROQ_DEFAULT_MODEL
from app.ai.validators import AIValidationError, assert_no_identifiers

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SECONDS = 10
MAX_TOKENS = 700
AUDIENCE = {"donor": "a donor", "grant": "a grant funder", "general": "the board and the community"}
TITLES = {"donor": "Donor report", "grant": "Grant report", "general": "Impact summary"}
OWNER_KEY = {
    "donor": "by_donor",
    "grant": "by_grant",
}  # general reports have no donor or grant split


@dataclass(frozen=True)
class ReportContent:
    title: str
    note: str | None  # shown when an AI draft was used
    story: list[str]
    figures: list[str]


def _ask_groq(prompt: str) -> str | None:
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        return None
    model = (os.getenv("GROQ_MODEL") or "").strip() or GROQ_DEFAULT_MODEL
    body: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": MAX_TOKENS,
    }
    if model.startswith(GPT_OSS_PREFIX):
        body["reasoning_effort"] = "low"
        body["include_reasoning"] = False
    try:  # one attempt only: a slow or rate-limited model must not slow the page
        response = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=body,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
        return None
    return text.strip() if isinstance(text, str) and text.strip() else None


def _prompt(preset: str, period: str, summary: dict[str, Any]) -> str:
    return (
        f"Write a short impact report for {AUDIENCE[preset]} for the food pantry Epic Cure, "
        f"covering {period}. Use 3 short paragraphs of plain prose, no headings or lists. "
        "Use only the numbers in the figures below, never invent or estimate any number, name "
        "or fact, and do not mention individuals.\n\nFigures (JSON):\n"
        + json.dumps(summary, separators=(",", ":"))
    )


def _template(preset: str, period: str, summary: dict[str, Any]) -> list[str]:
    lines = [
        f"Between {period}, Epic Cure served {summary['households']} households across "
        f"{summary['visits']} visits, distributing {summary['items']} items "
        f"({summary['pounds']} lb).",
    ]
    owners = summary.get(OWNER_KEY.get(preset, ""), [])
    if owners:
        top = owners[0]
        lines.append(
            f"The largest share came through {top['label']}: "
            f"{top['items']} items to {top['households']} households."
        )
    if summary["top_categories"]:
        names = ", ".join(f"{c['category']} ({c['items']})" for c in summary["top_categories"])
        lines.append(f"Most distributed categories: {names}.")
    return lines


def _figures(summary: dict[str, Any], preset: str) -> list[str]:
    lines = [
        f"Households served: {summary['households']}",
        f"Completed visits: {summary['visits']}",
        f"Items distributed: {summary['items']}",
        f"Pounds distributed: {summary['pounds']}",
        "Household sizes: " + ", ".join(f"{k}: {v}" for k, v in summary["household_sizes"].items()),
    ]
    lines += [
        f"{row['label']}: {row['items']} items, {row['pounds']} lb, {row['households']} households"
        for row in summary.get(OWNER_KEY.get(preset, ""), [])
    ]
    return lines


def report_content(preset: str, period: str, summary: dict[str, Any]) -> ReportContent:
    """The narrative (AI draft or template) plus the real figures it must agree with."""
    drafted: str | None = None
    try:
        assert_no_identifiers(summary)
        drafted = _ask_groq(_prompt(preset, period, summary))
    except AIValidationError:
        drafted = None  # never send anything identifier-like off the server
    story = (
        [p.strip() for p in drafted.split("\n\n") if p.strip()]
        if drafted
        else _template(preset, period, summary)
    )
    return ReportContent(
        title=f"{TITLES[preset]}: {period}",
        note="Drafted with AI from the figures below. Please review before sending."
        if drafted
        else None,
        story=story,
        figures=_figures(summary, preset),
    )
