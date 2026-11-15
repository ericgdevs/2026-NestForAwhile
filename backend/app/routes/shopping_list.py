from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.list_reader import read_list_photo
from app.ai.list_reader import VisionNotConfigured
from app.ai.provider import ProviderError
from app.auth import Role, require_roles
from app.db import get_db
from app.models import CartItem, Client, ShoppingListItem, User
from app.rules.classify import RESTRICTED, household_label
from app.services.cart import active_session, get_or_create_cart
from app.services.nutrition import members_for
from app.services.shopping_list import (
    aisle_order,
    find_same_line,
    first_lots,
    item_view,
    location_of,
    match_line,
    merge_into_line,
    split_lines,
)
from app.services.swaps import find_swaps

router = APIRouter()
client_only = require_roles(Role.CLIENT)
MAX_PHOTO_BYTES = 6_000_000


class ListLine(BaseModel):
    text: str = Field(min_length=1, max_length=120)
    product_id: int | None = None


class AddRequest(BaseModel):
    items: list[ListLine] = Field(min_length=1, max_length=50)
    recipe: dict | None = None  # set when adding a recipe's ingredients; shown as "For: <title>"


class TickRequest(BaseModel):
    ticked: bool


class ParseRequest(BaseModel):
    text: str | None = Field(default=None, max_length=5000)
    image_base64: str | None = None
    media_type: str = Field(default="image/jpeg", pattern=r"^image/(jpeg|png|webp|heic)$")

    @model_validator(mode="after")
    def one_source(self):
        if bool(self.text) == bool(self.image_base64):
            raise ValueError("Send either text or a photo")
        return self


def _items(database: Session, user: User) -> list[ShoppingListItem]:
    return list(
        database.scalars(select(ShoppingListItem).where(ShoppingListItem.client_id == user.id))
    )


def _list_view(database: Session, user: User) -> dict[str, list[dict[str, object]]]:
    members = members_for(database.get(Client, user.id))
    stocked = first_lots(database)
    views = [item_view(item, stocked, members) for item in _items(database, user)]
    return {"items": sorted(views, key=aisle_order)}


def _own(database: Session, user: User, item_id: int) -> ShoppingListItem:
    item = database.get(ShoppingListItem, item_id)
    if item is None or item.client_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List item not found")
    return item


@router.get("/shopping-list")
def get_list(user: User = Depends(client_only), database: Session = Depends(get_db)):
    return _list_view(database, user)


@router.post("/shopping-list", status_code=status.HTTP_201_CREATED)
def add_items(
    payload: AddRequest, user: User = Depends(client_only), database: Session = Depends(get_db)
):
    stocked = first_lots(database)
    existing = _items(database, user)
    for line in payload.items:
        product_id = line.product_id
        if product_id is None and (match := match_line(line.text, stocked)) is not None:
            product_id = match.id
        item = find_same_line(existing, product_id, line.text)
        if item is None:
            item = ShoppingListItem(client_id=user.id, product_id=product_id, text=line.text)
            item.source, item.recipe = "recipe" if payload.recipe else "you", []
            database.add(item)
            existing.append(item)
        merge_into_line(item, payload.recipe)
    database.commit()
    return _list_view(database, user)


@router.patch("/shopping-list/{item_id}")
def tick_item(
    item_id: int,
    payload: TickRequest,
    user: User = Depends(client_only),
    database: Session = Depends(get_db),
):
    """Ticking an in-stock product also puts one in the tracked cart (if it isn't there yet)."""
    item = _own(database, user, item_id)
    item.ticked = payload.ticked
    session = active_session(database, database.get(Client, user.id))
    if payload.ticked and item.product_id and session and item.product_id in first_lots(database):
        cart = get_or_create_cart(database, session)
        in_cart = database.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart.id, CartItem.product_id == item.product_id
            )
        )
        if in_cart is None:
            database.add(CartItem(cart_id=cart.id, product_id=item.product_id, quantity=1))
    database.commit()
    return _list_view(database, user)


@router.delete("/shopping-list/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int, user: User = Depends(client_only), database: Session = Depends(get_db)
):
    database.delete(_own(database, user, item_id))
    database.commit()


@router.post("/shopping-list/parse")
def parse_list(
    payload: ParseRequest, user: User = Depends(client_only), database: Session = Depends(get_db)
):
    """Typed text or a photo becomes suggested lines; nothing is saved, the photo is dropped."""
    if payload.image_base64:
        try:
            if len(base64.b64decode(payload.image_base64, validate=True)) > MAX_PHOTO_BYTES:
                raise HTTPException(status_code=413, detail="That photo is too large.")
        except binascii.Error as exc:
            raise HTTPException(status_code=422, detail="That photo couldn't be read.") from exc
        try:
            items = read_list_photo(payload.image_base64, payload.media_type)
        except VisionNotConfigured as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="We can't read photos right now. Please type your list instead.",
            ) from exc
        except ProviderError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="We couldn't read that photo. Try a clearer one, or type your list instead.",
            ) from exc
        # The shopping list has no quantity column, so a count rides along in the line text.
        lines = [f"{i.name} ×{i.quantity}" if i.quantity > 1 else i.name for i in items]
    else:
        lines = split_lines(payload.text or "")
    stocked = first_lots(database)
    members = members_for(database.get(Client, user.id))
    return {"lines": [_suggestion(database, line, stocked, members) for line in lines]}


def _suggestion(database: Session, line: str, stocked, members) -> dict[str, object]:
    """One reviewable line: the catalog match, its household status from the rules engine."""
    product = match_line(line, stocked)
    if product is None:
        return {"text": line, "product_id": None, "name": None, "status": None, "location": None}
    label = household_label(product, members)
    return {
        "text": line,
        "product_id": product.id,
        "name": product.name,
        "status": label["status"],
        "not_for": label["not_for"],
        "location": location_of(stocked.get(product.id)),
        "swaps": find_swaps(database, product, members) if label["status"] == RESTRICTED else [],
    }
