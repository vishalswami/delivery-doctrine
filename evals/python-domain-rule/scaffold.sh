#!/bin/bash
set -e
mkdir -p src/shop/orders tests
cat > pyproject.toml <<'PY'
[project]
name = "shop"
version = "0.1.0"
requires-python = ">=3.14"

[tool.pytest.ini_options]
pythonpath = ["src"]
PY
touch src/shop/__init__.py
cat > src/shop/orders/__init__.py <<'PY'
from shop.orders.service import EmptyOrderError, Line, Order, OrderService, OrderStore

__all__ = ["EmptyOrderError", "Line", "Order", "OrderService", "OrderStore"]
PY
cat > src/shop/orders/service.py <<'PY'
from dataclasses import dataclass
from typing import NewType, Protocol

CustomerId = NewType("CustomerId", str)


class OrderError(Exception):
    pass


class EmptyOrderError(OrderError):
    pass


@dataclass(frozen=True, slots=True)
class Line:
    sku: str
    cents: int


@dataclass(frozen=True, slots=True)
class Order:
    customer: CustomerId
    lines: tuple[Line, ...]

    @property
    def total_cents(self) -> int:
        return sum(line.cents for line in self.lines)


class OrderStore(Protocol):
    def save(self, order: Order) -> None: ...


class OrderService:
    def __init__(self, store: OrderStore) -> None:
        self._store = store

    def place(self, order: Order) -> None:
        if not order.lines:
            raise EmptyOrderError(order.customer)
        self._store.save(order)
PY
cat > tests/test_orders.py <<'PY'
import pytest

from shop.orders import EmptyOrderError, Order, OrderService
from shop.orders.service import CustomerId


class FakeOrderStore:
    def __init__(self) -> None:
        self.saved: list[Order] = []

    def save(self, order: Order) -> None:
        self.saved.append(order)


def test_given_an_order_without_lines_when_placed_then_refused() -> None:
    store = FakeOrderStore()
    service = OrderService(store)

    with pytest.raises(EmptyOrderError):
        service.place(Order(CustomerId("c-1"), ()))
PY
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "order service with empty-order check"
