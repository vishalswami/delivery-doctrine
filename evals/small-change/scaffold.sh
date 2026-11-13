#!/bin/bash
set -e
cat > booking.py <<'PY'
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Booking:
    room: str
    start: datetime
    end: datetime


def overlaps(a: Booking, b: Booking) -> bool:
    return a.room == b.room and a.start < b.end and b.start < a.end


class BookingService:
    def __init__(self) -> None:
        self.bookings: list[Booking] = []

    def reserve(self, booking: Booking) -> Booking:
        if any(overlaps(booking, existing) for existing in self.bookings):
            raise ValueError("overlap")
        self.bookings.append(booking)
        return booking
PY
cat > test_booking.py <<'PY'
from datetime import datetime

import pytest

from booking import Booking, BookingService


def test_given_existing_booking_when_reserving_overlapping_slot_then_rejected():
    service = BookingService()
    service.reserve(Booking("A", datetime(2026, 1, 1, 9), datetime(2026, 1, 1, 10)))

    with pytest.raises(ValueError):
        service.reserve(Booking("A", datetime(2026, 1, 1, 9, 30), datetime(2026, 1, 1, 11)))
PY
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "booking service with overlap check"
