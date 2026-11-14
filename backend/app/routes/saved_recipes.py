from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import SavedRecipe, User

router = APIRouter()
client_only = require_roles(Role.CLIENT)


class SaveRecipeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    cuisine: str | None = Field(default=None, max_length=30)
    ingredients: list[dict] = Field(min_length=1, max_length=40)
    steps: list[str] = Field(min_length=1, max_length=40)


def _view(row: SavedRecipe) -> dict[str, object]:
    return {"id": row.id, **row.recipe}


@router.get("/me/recipes")
def list_saved(user: User = Depends(client_only), database: Session = Depends(get_db)):
    rows = database.scalars(
        select(SavedRecipe)
        .where(SavedRecipe.client_id == user.id)
        .order_by(SavedRecipe.created_at.desc(), SavedRecipe.id.desc())
    )
    return [_view(row) for row in rows]


@router.post("/me/recipes", status_code=status.HTTP_201_CREATED)
def save_recipe(
    payload: SaveRecipeRequest,
    user: User = Depends(client_only),
    database: Session = Depends(get_db),
):
    row = SavedRecipe(client_id=user.id, title=payload.title, recipe=payload.model_dump())
    database.add(row)
    database.commit()
    return _view(row)


@router.delete("/me/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved(
    recipe_id: int,
    user: User = Depends(client_only),
    database: Session = Depends(get_db),
):
    row = database.get(SavedRecipe, recipe_id)
    if row is None or row.client_id != user.id:  # another household's recipe looks missing
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    database.delete(row)
    database.commit()
