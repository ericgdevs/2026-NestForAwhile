from datetime import date

from sqlmodel import Session

from app.schemas import LotRead
from app.services import fifo


def list_lots(session: Session, today: date | None = None) -> list[LotRead]:
    today = today or date.today()
    return [LotRead(lot_id=lot.id, product_id=lot.product_id, quantity=lot.quantity,
                    expiration_date=lot.expiration_date, expiring_soon=fifo.is_expiring_soon(lot, today))
            for lot in fifo.all_lots_fifo(session)]
