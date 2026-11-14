from datetime import UTC, datetime, timedelta

from sqlmodel import select

from app.models import Cart, CartItem, InventoryLot, Product
from app.services import checkout, sessions
from tests.unit.test_queue import client_id

VEGAN_NUT_ALLERGY_PERSONA = 3


def add_product(session, name, qty, allergens=(), expires_in_days=30, weight_lb=1.0):
    product = Product(sku=name, barcode=name, name=name, category="x", allergens=list(allergens),
                      diet_flags=["vegan"], ingredients_text="rice", weight_lb=weight_lb)
    session.add(product)
    session.flush()
    session.add(InventoryLot(product_id=product.id, quantity=qty, received_at=datetime(2026, 1, 1, tzinfo=UTC),
                             expiration_date=(datetime.now(UTC) + timedelta(days=expires_in_days)).date()))
    session.commit()
    return product


def start_with_cart(seeded, lines):
    shopping = sessions.start_session(seeded, client_id(seeded, VEGAN_NUT_ALLERGY_PERSONA))
    cart = Cart(session_id=shopping.id)
    seeded.add(cart)
    seeded.flush()
    seeded.add_all(CartItem(cart_id=cart.id, product_id=p.id, quantity=qty) for p, qty in lines)
    seeded.commit()
    return shopping


def test_clean_cart_has_no_blocks(seeded):
    shopping = start_with_cart(seeded, [(add_product(seeded, "Rice", 5), 2)])
    assert checkout.find_blocked_items(seeded, shopping) == []


def test_restricted_item_is_blocked(seeded):
    nuts = add_product(seeded, "Peanut Butter", 5, allergens=["peanuts"])
    shopping = start_with_cart(seeded, [(add_product(seeded, "Rice", 5), 1), (nuts, 1)])
    blocked = checkout.find_blocked_items(seeded, shopping)
    assert [(b.product_id, b.status) for b in blocked] == [(nuts.id, "Restricted")]


def test_shortfall_is_blocked_and_expired_stock_does_not_count(seeded):
    short = add_product(seeded, "Rice", 2)
    expired = add_product(seeded, "Old Rice", 9, expires_in_days=-1)
    shopping = start_with_cart(seeded, [(short, 3), (expired, 1)])
    assert {b.product_id for b in checkout.find_blocked_items(seeded, shopping)} == {short.id, expired.id}


def test_unknown_product_is_blocked(seeded):
    shopping = start_with_cart(seeded, [])
    cart = seeded.exec(select(Cart).where(Cart.session_id == shopping.id)).one()
    seeded.add(CartItem(cart_id=cart.id, product_id=999999, quantity=1))  # SQLite does not enforce the FK
    seeded.commit()
    assert [b.product_id for b in checkout.find_blocked_items(seeded, shopping)] == [999999]
