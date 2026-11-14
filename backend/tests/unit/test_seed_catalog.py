from datetime import date

from sqlmodel import select

from app.models import DonationSource, GrantFundingStream, InventoryLocation, InventoryLot, Product
from seed.catalog import PRODUCTS
from seed.load import seed_all

NUTRIENTS = ["calories", "sodium_mg", "sugar_g", "added_sugar_g", "sat_fat_g", "fiber_g", "protein_g",
             "potassium_mg", "phosphorus_mg", "carbs_g"]


def test_seed_data_is_well_formed():
    assert len({p["barcode"] for p in PRODUCTS}) == len(PRODUCTS)
    assert len({p["sku"] for p in PRODUCTS}) == len(PRODUCTS)
    for p in PRODUCTS:
        assert all(n in p for n in NUTRIENTS) and len(p["location"]) == 3


def test_catalog_loads_with_locations_lots_and_attribution(session):
    seed_all(session)
    assert len(session.exec(select(Product)).all()) == len(PRODUCTS)
    assert session.exec(select(InventoryLocation)).first().aisle
    lots = session.exec(select(InventoryLot)).all()
    assert len(lots) == len(PRODUCTS)
    expiries = {lot.expiration_date for lot in lots}
    assert any(e < date.today() for e in expiries) and any(e > date.today() for e in expiries)
    assert session.exec(select(DonationSource)).first() and session.exec(select(GrantFundingStream)).first()


def test_catalog_seed_is_idempotent(session):
    seed_all(session)
    seed_all(session)
    assert len(session.exec(select(InventoryLot)).all()) == len(PRODUCTS)
