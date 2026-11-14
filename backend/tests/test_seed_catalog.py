from datetime import date, timedelta

from cryptography.fernet import Fernet
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Donor, Grant, InventoryLot, Product
from seed.load import seed_catalog, seed_users


def test_seed_catalog_creates_synthetic_products_lots_donors_and_grants(monkeypatch):
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", Fernet.generate_key().decode())
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as database:
        seed_users(database)
        seed_catalog(database)
        products = database.scalars(select(Product)).all()
        lots = database.scalars(select(InventoryLot)).all()
        donors = database.scalars(select(Donor)).all()
        grants = database.scalars(select(Grant)).all()

    assert len(products) == 4
    assert all(product.barcode.startswith("000000") for product in products)
    assert len(lots) == 8
    assert len({lot.expiration_date for lot in lots}) > 1
    assert any(lot.expiration_date <= date.today() + timedelta(days=5) for lot in lots)
    assert all(lot.reorder_threshold == 4 for lot in lots)
    assert len(donors) == 2
    assert len(grants) == 2
