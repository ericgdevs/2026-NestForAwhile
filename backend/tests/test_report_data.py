from datetime import datetime
from io import BytesIO
from xml.etree import ElementTree
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import (
    Checkout,
    CheckoutItem,
    Client,
    Donor,
    Grant,
    InventoryLot,
    ShoppingSession,
    Visit,
)
from app.services import report_narrative
from app.services.report_data import participant_code


def _visit(database, client_id, lot, quantity, when):
    """One completed visit that took `quantity` of the lot's product (synthetic)."""
    session = ShoppingSession(
        Shopping_Session_Token=f"synthetic-report-{client_id}-{lot.id}-{when:%m%d}",
        client_id=client_id,
        status="completed",
    )
    database.add(session)
    database.flush()
    checkout = Checkout(
        session_id=session.id, validated_by=client_id, status="completed", total_lb=1
    )
    database.add(checkout)
    database.flush()
    database.add(
        CheckoutItem(
            checkout_id=checkout.id,
            product_id=lot.product_id,
            lot_id=lot.id,
            quantity=quantity,
            status_at_checkout="Approved",
        )
    )
    database.add(
        Visit(
            client_id=client_id,
            session_id=session.id,
            started_at=when,
            completed_at=when,
            pounds_distributed=1,
        )
    )
    database.commit()


@pytest.fixture
def world(database, logged_in_client):
    """Two households: one visit with donor stock in March, one with grant stock in April."""
    first, second = database.query(Client).limit(2).all()
    first.Household_Size, second.Household_Size = 1, 5
    donor, grant = (
        Donor(name="Synthetic Donor", attribution_label="Synthetic Donor Co"),
        Grant(name="Synthetic Grant", attribution_label="Synthetic Grant Fund"),
    )
    database.add_all([donor, grant])
    database.flush()
    database.query(InventoryLot).update(
        {"donor_id": None, "grant_id": None}
    )  # seed lots are attributed
    lots = database.query(InventoryLot).limit(2).all()
    lots[0].donor_id, lots[1].grant_id = donor.id, grant.id
    database.commit()
    _visit(database, first.user_id, lots[0], 3, datetime(2026, 3, 10, 12))
    _visit(database, second.user_id, lots[1], 4, datetime(2026, 4, 10, 12))
    return {
        "donor": donor,
        "first": first,
        "second": second,
        "lots": lots,
        "login": logged_in_client,
    }


def _get(database, login, path, role=Role.WAREHOUSE_MANAGER, method="get"):
    app.dependency_overrides[get_db] = lambda: database
    try:
        return getattr(TestClient(app), method)(path, cookies=login(role).cookies)
    finally:
        app.dependency_overrides.clear()


def test_preview_rows_are_anonymous_and_totals_cover_every_match(database, world):
    body = _get(database, world["login"], "/reports/preview").json()
    assert body["totals"]["visits"] == 2 and body["totals"]["households"] == 2
    assert body["totals"]["items"] == 7
    row = body["rows"][0]
    assert set(row) == {
        "participant_id",
        "visit_date",
        "household_size",
        "items",
        "pounds",
        "donors",
        "grants",
    }
    assert row["participant_id"].startswith("P-") and len(row["participant_id"]) == 10
    assert {r["household_size"] for r in body["rows"]} == {1, 5}  # a household of one is kept


def test_participant_code_is_stable_and_hides_the_database_id():
    assert participant_code(7) == participant_code(7) != participant_code(8)


def test_filters_narrow_the_preview(database, world):
    login = world["login"]

    def count(query):
        return len(_get(database, login, f"/reports/preview?{query}").json()["rows"])

    assert count("attributed=donor") == 1
    assert count("attributed=grant") == 1
    assert count("date_from=2026-04-01") == 1
    assert count("date_to=2026-03-31") == 1
    assert count("household_min=2") == 1
    assert count("household_max=1") == 1
    category = world["lots"][0].product.category
    assert count(f"category={category}") >= 1
    assert count(f"donor_id={world['donor'].id}") == 1
    assert count("date_from=2027-01-01") == 0


def test_bad_filters_are_rejected(database, world):
    assert (
        _get(
            database, world["login"], "/reports/preview?date_from=2026-05-01&date_to=2026-04-01"
        ).status_code
        == 422
    )
    assert (
        _get(
            database, world["login"], "/reports/preview?household_min=5&household_max=2"
        ).status_code
        == 422
    )


def test_clients_cannot_read_reports_but_directors_can(database, world):
    assert _get(database, world["login"], "/reports/preview", Role.CLIENT).status_code == 403
    assert _get(database, world["login"], "/reports/preview", Role.DIRECTOR).status_code == 200
    labels = [
        d["label"]
        for d in _get(database, world["login"], "/reports/options", Role.DIRECTOR).json()["donors"]
    ]
    assert "Synthetic Donor Co" in labels


def test_export_csv_and_json_match_the_preview(database, world):
    csv_body = _get(database, world["login"], "/reports/export?format=csv&attributed=donor")
    lines = csv_body.text.strip().splitlines()
    assert lines[0] == "participant_id,visit_date,household_size,items,pounds,donors,grants"
    assert len(lines) == 2 and "Synthetic Donor Co" in lines[1]
    rows = _get(database, world["login"], "/reports/export?format=json").json()
    assert len(rows) == 2 and "client_id" not in rows[0] and "name" not in rows[0]


def _docx_text(response):
    with ZipFile(BytesIO(response.content)) as archive:
        return archive.read("word/document.xml").decode()


def test_written_report_falls_back_to_a_template_without_ai(database, world, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    response = _get(
        database,
        world["login"],
        "/reports/written?preset=donor&attributed=donor&date_from=2026-03-01&date_to=2026-04-30",
        method="post",
    )
    text = _docx_text(response)
    assert response.status_code == 200
    assert "Donor report" in text and "Figures" in text and "Synthetic Donor Co" in text
    assert "Drafted with AI" not in text and "P-" not in text


def test_written_report_uses_the_ai_draft_but_only_sends_aggregates(database, world, monkeypatch):
    sent = []
    monkeypatch.setattr(
        report_narrative,
        "_ask_groq",
        lambda prompt: sent.append(prompt) or "Synthetic story.\n\nSecond paragraph.",
    )
    response = _get(
        database,
        world["login"],
        "/reports/written?preset=grant&attributed=grant&date_from=2026-03-01&date_to=2026-04-30",
        method="post",
    )
    text = _docx_text(response)
    assert "Synthetic story." in text and "Drafted with AI" in text and "Figures" in text
    assert "P-" not in sent[0] and "participant" not in sent[0]
    assert (
        _get(database, world["login"], "/reports/written?preset=other", method="post").status_code
        == 422
    )


# --- written reports: charts, PDF, Word, both ---
def _written(database, world, query, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    path = f"/reports/written?{query}&date_from=2026-03-01&date_to=2026-04-30"
    return _get(database, world["login"], path, method="post")


def test_word_report_embeds_the_charts_with_alt_text(database, world, monkeypatch):
    response = _written(database, world, "preset=donor&attributed=donor", monkeypatch)
    with ZipFile(BytesIO(response.content)) as archive:
        names = archive.namelist()
        document = archive.read("word/document.xml").decode()
        rels = archive.read("word/_rels/document.xml.rels").decode()
        for part in names:
            if part.endswith((".xml", ".rels")):
                ElementTree.fromstring(archive.read(part))  # every XML part is well formed
        pngs = [n for n in names if n.startswith("word/media/") and n.endswith(".png")]
    assert (
        len(pngs) >= 3
        and "<w:drawing>" in document
        and 'descr="Items distributed per week' in document
    )
    assert all(f"media/chart{n}.png" in rels for n in range(1, len(pngs) + 1))
    assert "P-" not in document


def test_pdf_report_is_a_real_pdf_with_the_charts(database, world, monkeypatch):
    response = _written(database, world, "preset=grant&attributed=grant&format=pdf", monkeypatch)
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].endswith('grant-report.pdf"')
    assert response.content.startswith(b"%PDF") and response.content.count(b"/Subtype /Image") >= 3


def test_both_formats_come_as_one_zip_with_matching_files(database, world, monkeypatch):
    response = _written(database, world, "preset=general&format=both", monkeypatch)
    assert response.headers["content-type"] == "application/zip"
    with ZipFile(BytesIO(response.content)) as archive:
        assert sorted(archive.namelist()) == ["general-report.docx", "general-report.pdf"]
        assert archive.read("general-report.pdf").startswith(b"%PDF")
        with ZipFile(BytesIO(archive.read("general-report.docx"))) as word:
            assert "Impact summary" in word.read("word/document.xml").decode()


def test_unknown_format_or_audience_is_rejected(database, world):
    login = world["login"]
    assert (
        _get(database, login, "/reports/written?preset=donor&format=exe", method="post").status_code
        == 422
    )
    assert (
        _get(database, login, "/reports/written?preset=press&format=pdf", method="post").status_code
        == 422
    )


def test_weekly_series_groups_visits_by_week(database, world):
    from datetime import date

    from app.services.report_data import ReportFilters, weekly

    weeks = weekly(database, ReportFilters())
    assert [w["week"] for w in weeks] == [date(2026, 3, 9), date(2026, 4, 6)]
    assert [w["items"] for w in weeks] == [3, 4] and all(w["visits"] == 1 for w in weeks)


def test_charts_skip_empty_data_and_report_their_values_as_text():
    from datetime import date

    from app.services.report_charts import charts_for

    summary = {
        "top_categories": [{"category": "Produce", "items": 5}],
        "household_sizes": {"1 person": 0, "2 people": 0},
        "by_donor": [],
        "by_grant": [],
    }
    charts = charts_for("donor", summary, [{"week": date(2026, 3, 9), "visits": 1, "items": 3}])
    assert [c.title for c in charts] == [
        "Items distributed per week",
        "Most distributed categories",
    ]
    assert charts[1].alt == "Most distributed categories: Produce 5" and charts[0].png.startswith(
        b"\x89PNG"
    )


def test_pdf_survives_the_typographic_characters_an_ai_draft_uses():
    from app.services.report_narrative import ReportContent
    from app.services.report_pdf import build_report_pdf

    content = ReportContent("Impact — “Q1”", None, ["It’s 5 households … ok •"], ["Figures – 1 ✓"])
    assert build_report_pdf(content, []).startswith(b"%PDF")
