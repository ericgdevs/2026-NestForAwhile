from sqlmodel import select

from app.models import InventoryLot, Product
from app.services import recommendations, sessions
from tests.unit.test_queue import client_id


def recs_for(session, persona):
    cid = client_id(session, persona)
    shopping = sessions.start_session(session, cid)
    return {r.name: r for r in recommendations.list_for_session(session, cid, shopping.id)}


def test_never_restricted_and_expired_excluded(seeded):
    recs = recs_for(seeded, 0)  # diabetes + hypertension
    assert "Canned Tomato Soup" not in recs  # sodium 700 is Restricted
    assert "Whole Milk" not in recs  # expired lot
    assert all(r.status in ("Approved", "Capped") for r in recs.values())


def test_quantity_scales_with_household_and_capped_gets_one(seeded):
    recs = recs_for(seeded, 0)  # household 4
    assert recs["Rolled Oats"].status == "Approved" and recs["Rolled Oats"].suggested_qty == 4
    assert recs["Peanut Butter"].status == "Capped" and recs["Peanut Butter"].suggested_qty == 1


def test_allergy_and_diet_exclusions(seeded):
    recs = recs_for(seeded, 3)  # vegan + nut allergy, household 6
    assert "Peanut Butter" not in recs and "Frozen Chicken Breast" not in recs
    assert recs["Rolled Oats"].suggested_qty == 6


def test_quantity_limited_by_stock(seeded):
    lot = seeded.exec(select(InventoryLot).join(Product).where(Product.name == "Rolled Oats")).one()
    lot.quantity = 2
    seeded.add(lot)
    seeded.commit()
    assert recs_for(seeded, 3)["Rolled Oats"].suggested_qty == 2


def test_out_of_stock_and_expired_lots_excluded(seeded):
    for lot in seeded.exec(select(InventoryLot)):
        lot.quantity = 0
        seeded.add(lot)
    seeded.commit()
    assert recs_for(seeded, 3) == {}


def test_deterministic_order_expiring_soonest_first(seeded):
    names = list(recs_for(seeded, 3))
    assert names[0] == "Whole Wheat Bread"  # expires in 6 days, before oats (180)
