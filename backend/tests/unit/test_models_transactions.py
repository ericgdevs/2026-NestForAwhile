from app.models import (
    CapacitySetting,
    Cart,
    CartItem,
    Checkout,
    CheckoutItem,
    Intervention,
    QueueEntry,
    Recommendation,
    ShoppingSession,
)


def test_session_and_transaction_models_keep_official_fields():
    assert ShoppingSession.__table__.c.Shopping_Session_Token.unique is True
    assert CapacitySetting.__table__.c.Max_Floor_Capacity is not None
    assert QueueEntry.__table__.c.status is not None
    assert Cart.__table__.c.session_id.unique is True
    assert CartItem.__table__.c.quantity is not None
    assert Recommendation.__table__.c.suggested_qty is not None
    assert Checkout.__table__.c.status is not None
    assert CheckoutItem.__table__.c.lot_id is not None
    assert Intervention.__table__.c.action is not None
