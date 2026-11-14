from app.models import AuditEvent, InventoryLot, InventoryMovement, Product


def test_catalog_and_inventory_models_expose_required_fields():
    assert Product.__tablename__ == "products"
    assert Product.__table__.c.barcode.unique is True
    assert InventoryLot.__table__.c.expiration_date is not None
    assert InventoryLot.__table__.c.aisle is not None
    assert InventoryLot.__table__.c.shelf is not None
    assert InventoryLot.__table__.c.bin is not None
    assert InventoryMovement.__table__.c.reason is not None
    assert AuditEvent.__table__.c.variance is not None
