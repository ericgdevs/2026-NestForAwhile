from datetime import timedelta

import pytest
from fastapi import HTTPException
from sqlmodel import select

from app.auth import email_digest
from app.models import QueueEntry, QueueStatus, SessionStatus, User, utcnow
from app.services import capacity, queue, sessions
from seed.personas import PERSONAS


def client_id(session, n):
    return session.exec(select(User).where(User.email_hash == email_digest(PERSONAS[n]["email"]))).one().id


@pytest.fixture
def full_floor(seeded):
    capacity.set_max_capacity(seeded, 1, user_id=1)
    sessions.start_session(seeded, client_id(seeded, 0))
    return seeded


def test_waiting_clients_are_fifo(full_floor):
    a, b = client_id(full_floor, 1), client_id(full_floor, 2)
    queue.join_queue(full_floor, a)
    queue.join_queue(full_floor, b)
    assert queue.queue_state(full_floor, a).position == 1
    assert queue.queue_state(full_floor, b).position == 2
    assert capacity.queue_waiting(full_floor) == 2


def test_join_twice_does_not_duplicate(full_floor):
    a = client_id(full_floor, 1)
    assert queue.join_queue(full_floor, a).id == queue.join_queue(full_floor, a).id


def test_ending_session_promotes_oldest_waiting_only(full_floor):
    a, b = client_id(full_floor, 1), client_id(full_floor, 2)
    queue.join_queue(full_floor, a)
    queue.join_queue(full_floor, b)
    sessions.end_session(full_floor, client_id(full_floor, 0))
    assert queue.queue_state(full_floor, a).status == QueueStatus.READY
    assert queue.queue_state(full_floor, b).status == QueueStatus.WAITING
    assert capacity.active_floor_shoppers(full_floor) == 1  # ready spot counts toward the floor


def test_claim_turns_ready_spot_into_session(full_floor):
    a = client_id(full_floor, 1)
    queue.join_queue(full_floor, a)
    sessions.end_session(full_floor, client_id(full_floor, 0))
    shopping = sessions.claim_turn(full_floor, a)
    assert shopping.status == SessionStatus.ACTIVE
    assert capacity.active_floor_shoppers(full_floor) == 1


def test_claim_when_not_ready_is_409(full_floor):
    a = client_id(full_floor, 1)
    queue.join_queue(full_floor, a)
    with pytest.raises(HTTPException) as e:
        sessions.claim_turn(full_floor, a)
    assert e.value.status_code == 409


def test_unclaimed_spot_expires_and_next_is_promoted(full_floor):
    a, b = client_id(full_floor, 1), client_id(full_floor, 2)
    queue.join_queue(full_floor, a)
    queue.join_queue(full_floor, b)
    sessions.end_session(full_floor, client_id(full_floor, 0))
    entry = queue.current_entry(full_floor, a)
    entry.ready_at = utcnow() - timedelta(minutes=30)
    full_floor.add(entry)
    full_floor.commit()
    queue.refresh_queue(full_floor)
    assert queue.current_entry(full_floor, a) is None
    assert queue.queue_state(full_floor, b).status == QueueStatus.READY
    with pytest.raises(HTTPException) as e:
        sessions.claim_turn(full_floor, a)
    assert e.value.status_code == 409


def test_raising_capacity_promotes_waiting(full_floor):
    a = client_id(full_floor, 1)
    queue.join_queue(full_floor, a)
    capacity.set_max_capacity(full_floor, 2, user_id=1)
    queue.refresh_queue(full_floor)
    assert queue.queue_state(full_floor, a).status == QueueStatus.READY
