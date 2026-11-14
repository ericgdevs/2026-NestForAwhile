from app.models import AIRequest, Donor, Grant, Report


def test_reporting_and_ai_models_are_aggregate_safe():
    assert Donor.__table__.c.attribution_label is not None
    assert Grant.__table__.c.attribution_label is not None
    assert Report.__table__.c.period_start is not None
    assert Report.__table__.c.period_end is not None
    assert AIRequest.__table__.c.used_fallback is not None
    assert "email" not in AIRequest.__table__.columns
