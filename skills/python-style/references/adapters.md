# Python adapters

Read when the slice touches an adapter: persistence, an HTTP handler or a message consumer.
The feature package (`src/shop/orders/`) declares its ports as `Protocol`s; adapters sit beside
it by mechanism (`orders/postgres.py`, `orders/httpapi.py`) and satisfy them structurally.
House names win (`delivery-doctrine:python-style`).

## Persistence: the port and the unit of work

The consumer declares the port with domain types in and out. No connection, cursor, ORM row or
pydantic model crosses it.

```python
class OrderStore(Protocol):
    def get(self, order_id: OrderId) -> Order: ...
    def save(self, order: Order) -> None: ...
    def release(self, order_id: OrderId, at: datetime) -> None: ...
```

One port call is one unit of work, and the adapter method owns its transaction. psycopg's
`with conn.transaction():` commits on a normal exit and rolls back when the block raises.

**The atomic SQL guard is legitimate.** A rule the database can enforce in one statement is
enforced there, so two concurrent releases cannot both win a read-update-persist race. The
domain method (`order.status(now)`) mirrors the rule and one test pins the two together; when a
house records the SQL-only guard as deliberate, it is not a finding.

```python
RELEASE_OPEN: Final = (
    "UPDATE orders SET released_at = %s WHERE id = %s AND released_at IS NULL"
)


class PostgresOrderStore:
    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def release(self, order_id: OrderId, at: datetime) -> None:
        with self._conn.transaction():
            released = self._conn.execute(RELEASE_OPEN, (at, order_id)).rowcount
        if released == 0:
            raise OrderNotOpenError(order_id)
```

Zero rows covers both "already released" and "no such order"; read back only when callers
branch on the difference.

**A use case spanning several port calls** first asks whether one port method can name the
unit (`place_with_reservation`); usually it can. When it cannot, the domain declares a unit of
work as a context-manager port, and the adapter yields a store bound to one transaction:

```python
class Transactions(Protocol):
    def begin(self) -> AbstractContextManager[OrderStore]: ...


class PostgresTransactions:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    @contextmanager
    def begin(self) -> Iterator[PostgresOrderStore]:
        with self._pool.connection() as conn, conn.transaction():
            yield PostgresOrderStore(conn)
```

The service reads as the unit it is; leaving the block commits, an exception rolls back:

```python
def cancel(self, order_id: OrderId, now: datetime) -> None:
    with self._transactions.begin() as orders:
        order = orders.get(order_id)
        order.cancel(now)
        orders.save(order)
```

`AbstractContextManager` is covariant, so `begin` returning the concrete store still satisfies
the port, and mypy checks the fit where the composition root passes it in. With SQLAlchemy the
adapter's block is `with Session(engine) as session, session.begin():`; the port is the same.
ORM models are adapter types, mapped to domain dataclasses through the domain constructor, so a
corrupt row fails loudly. Migrations use the house's tool (alembic is common).

## HTTP handler

pydantic models are adapter DTOs: they validate the wire shape and map to a domain command;
the domain never imports them.

```python
class PlaceOrderRequest(BaseModel):
    customer: str
    cents: int

    def to_command(self) -> PlaceOrder:
        return PlaceOrder.create(CustomerId(self.customer), self.cents)


class PlaceOrderResponse(BaseModel):
    id: str
```

The handler is thin: decode, build the command, call the service, return the DTO. The router
closes over the service the composition root built, so no `Depends` chain or module global
reaches for it.

```python
def order_routes(orders: OrderService) -> APIRouter:
    router = APIRouter()

    @router.post("/orders", status_code=201)
    def place(request: PlaceOrderRequest) -> PlaceOrderResponse:
        order_id = orders.place(request.to_command())
        return PlaceOrderResponse(id=order_id)

    return router
```

A plain `def` endpoint runs in FastAPI's threadpool, right for a blocking driver; `async def`
only when everything it calls awaits (`references/concurrency-security.md`).

## Errors to status, at the edge, once

Domain errors share a base per bounded context, so one handler maps the family:

```python
def status_of(error: OrderError) -> int:
    match error:
        case OrderNotFoundError():
            return 404
        case CreditLimitExceededError() | InvalidAmountError():
            return 422
        case _:
            return 400


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(OrderError)
    async def order_error(request: Request, exc: OrderError) -> JSONResponse:
        return JSONResponse(status_code=status_of(exc), content={"detail": str(exc)})
```

Anything that is not an `OrderError` is unexpected: no catch-all swallows it, the framework
answers 500 and the server logs it once. A second front-end over the same service maps with its
own function over the same error classes, so the two cannot diverge silently. A house error body
replaces the `{"detail": ...}` shape; the mapping stays in one place.

## Message consumer

An inbound adapter like the handler, in its own module (`orders/kafka.py`, or the house's
`consumers`), holding the concrete service.

- **Decode into a DTO, then the domain constructor.** A payload that fails either is poison:
  skip and count it, or dead-letter it where the house has a DLQ; never retry it.
- **Delivery is at least once**, so the use case is idempotent on a key the message carries
  (event ID as request ID), enforced by a unique constraint and `ON CONFLICT DO NOTHING`; a
  redelivery is a no-op, not an error.
- **Classify once**: an `OrderError` is an outcome (log, move on); anything else propagates so
  the client library retries or holds the offset, per its contract.
- **Publishing** writes an outbox row in the same transaction as the state change; a relay
  sends it. No broker call inside a database transaction.
