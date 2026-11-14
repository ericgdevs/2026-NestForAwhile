from datetime import date, timedelta

from sqlmodel import select

from app.models import DonationSource, GrantFundingStream, InventoryLot
from app.services import checkout, reports
from tests.unit.test_checkout_validation import add_product, start_with_cart

TODAY = date.today()
WIDE = (TODAY - timedelta(days=1), TODAY + timedelta(days=1))


def _linked_product(seeded, name, qty, donor=None, grant=None, weight_lb=1.0):
    product = add_product(seeded, name, qty, weight_lb=weight_lb)
    lot = seeded.exec(select(InventoryLot).where(InventoryLot.product_id == product.id)).one()
    lot.donor_id, lot.grant_id = donor, grant
    seeded.add(lot)
    seeded.commit()
    return product


def _complete(seeded, lines):
    shopping = start_with_cart(seeded, lines)
    assert checkout.complete_checkout(seeded, shopping.Shopping_Session_Token, user_id=1).status == "completed"


def test_attribution_comes_from_grant_linked_lots(seeded):
    donor = seeded.exec(select(DonationSource)).first().id
    grant = seeded.exec(select(GrantFundingStream)).first().id
    funded = _linked_product(seeded, "Rice", 10, donor=donor, grant=grant, weight_lb=2.0)
    unfunded = _linked_product(seeded, "Beans", 10, donor=donor)
    _complete(seeded, [(funded, 3), (unfunded, 2)])
    (grant_row, *_) = reports.source_attribution(seeded, "grant", *WIDE)
    assert (grant_row.units_distributed, grant_row.pounds_distributed) == (3, 6.0)
    donor_row = reports.source_attribution(seeded, "donor", *WIDE)[0]
    assert (donor_row.units_distributed, donor_row.pounds_distributed) == (5, 8.0)
    assert donor_row.on_hand_units >= 15  # remaining stock of both new lots plus seeded lots


def test_unlinked_lots_reported_as_unattributed(seeded):
    _complete(seeded, [(_linked_product(seeded, "Rice", 5), 1)])
    rows = reports.source_attribution(seeded, "donor", *WIDE)
    assert rows[-1].label == reports.UNATTRIBUTED and rows[-1].units_distributed == 1


def test_period_filter_excludes_other_days(seeded):
    _complete(seeded, [(_linked_product(seeded, "Rice", 5), 1)])
    past = (TODAY - timedelta(days=30), TODAY - timedelta(days=20))
    assert reports.visit_metrics(seeded, *past).visits_completed == 0
    assert reports.distribution_totals(seeded, *past) == []
    assert reports.visit_metrics(seeded, *WIDE).visits_completed == 1


def test_distribution_and_visit_totals(seeded):
    _complete(seeded, [(_linked_product(seeded, "Rice", 5, weight_lb=1.5), 2)])
    assert [(r.category, r.units, r.pounds) for r in reports.distribution_totals(seeded, *WIDE)] == [("x", 2, 3.0)]
    metrics = reports.visit_metrics(seeded, *WIDE)
    assert (metrics.families_served, metrics.pounds_distributed) == (1, 3.0)


def test_build_report_has_four_sections_and_is_deterministic(seeded):
    _complete(seeded, [(_linked_product(seeded, "Rice", 5, weight_lb=1.0), 2)])
    first, second = (reports.build_report(seeded, "grant", *WIDE) for _ in range(2))
    assert first == second and first.model_dump_json() == second.model_dump_json()
    assert set(first.model_dump()) == {"type", "period_start", "period_end", "donor_metrics", "grant_attribution",
                                       "distribution_totals", "visit_metrics"}


def test_build_report_has_no_identifiers(seeded):
    from seed.personas import PERSONAS

    _complete(seeded, [(_linked_product(seeded, "Rice", 5), 1)])
    text = reports.build_report(seeded, "donor", *WIDE).model_dump_json().lower()
    banned = [p["name"] for p in PERSONAS] + [p["email"] for p in PERSONAS] + ["@", "client", "email", "phone", "session"]
    assert not [b for b in banned if b.lower() in text]


def test_build_report_rejects_bad_input(seeded):
    import pytest

    with pytest.raises(ValueError):
        reports.build_report(seeded, "other", *WIDE)
    with pytest.raises(ValueError):
        reports.build_report(seeded, "donor", WIDE[1], WIDE[0])
