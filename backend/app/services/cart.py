from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import Cart, CartItem, Client, Product, Recommendation, ShoppingSession


def active_session(database: Session, client: Client) -> ShoppingSession | None:
    return database.scalar(
        select(ShoppingSession)
        .where(ShoppingSession.client_id == client.user_id, ShoppingSession.status == "active")
        .order_by(ShoppingSession.started_at.desc())
    )


def get_or_create_cart(database: Session, session: ShoppingSession) -> Cart:
    cart = database.scalar(select(Cart).where(Cart.session_id == session.id))
    if cart is None:
        cart = Cart(session_id=session.id)
        database.add(cart)
        try:
            database.flush()
        except IntegrityError:  # a parallel request created this session's cart first
            database.rollback()
            cart = database.scalar(select(Cart).where(Cart.session_id == session.id))
    return cart


def build_manifest(database: Session, cart: Cart) -> list[dict[str, object]]:
    items = database.scalars(
        select(CartItem).options(joinedload(CartItem.cart)).where(CartItem.cart_id == cart.id)
    ).all()
    products = {
        product.id: product
        for product in database.scalars(
            select(Product).where(Product.id.in_([item.product_id for item in items]))
        )
    }
    recommended_ids = {
        recommendation.product_id
        for recommendation in database.scalars(
            select(Recommendation).where(Recommendation.session_id == cart.session_id)
        )
    }
    return [
        {
            "product_id": item.product_id,
            "name": products[item.product_id].name,
            "quantity": item.quantity,
            "from_recommendation": item.from_recommendation or item.product_id in recommended_ids,
        }
        for item in items
    ]
