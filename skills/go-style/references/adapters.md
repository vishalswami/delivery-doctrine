# Go adapters

Read when the slice touches an adapter: persistence, an HTTP handler or a message consumer.
The domain package (`internal/order`) declares the ports; each adapter is a subpackage named
for its mechanism and satisfies them implicitly. House names win (`delivery-doctrine:go-style`).

## Persistence: the port and the transaction

The consumer declares the port, `ctx` first, domain types in and out. No `*sql.Tx`, ORM model
or generated row type crosses it, and no transaction is hidden in `ctx`.

```go
type Store interface {
	Place(ctx context.Context, o Order) error
	Release(ctx context.Context, id ID, at time.Time) error
	Find(ctx context.Context, id ID) (Order, error)
}
```

One port call is one unit of work, and the adapter method owns its transaction. A method that
writes twice (the order and its lines) opens and commits it; the deferred `Rollback` is a
no-op after `Commit` (it returns `sql.ErrTxDone`), which is why its error is dropped.

```go
var _ order.Store = (*Store)(nil)

func (s *Store) Place(ctx context.Context, o order.Order) error {
	tx, err := s.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("beginning place of order %s: %w", o.ID(), err)
	}
	defer func() { _ = tx.Rollback() }()

	if _, err := tx.ExecContext(ctx, insertOrder, o.ID(), o.Customer(), o.Total().Cents()); err != nil {
		return fmt.Errorf("inserting order %s: %w", o.ID(), err)
	}
	for _, l := range o.Lines() {
		if _, err := tx.ExecContext(ctx, insertLine, o.ID(), l.SKU(), l.Cents()); err != nil {
			return fmt.Errorf("inserting line %s of order %s: %w", l.SKU(), o.ID(), err)
		}
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("committing order %s: %w", o.ID(), err)
	}
	return nil
}
```

**The atomic SQL guard is legitimate.** A rule the database can enforce in one statement
(`released_at IS NULL`) is enforced there, so two concurrent releases cannot both win a
read-update-persist race. The domain method (`o.Status(now)`) mirrors the rule and one test
pins the two together; when a house records the SQL-only guard as deliberate, it is not a
finding.

```go
const releaseOpen = `UPDATE orders SET released_at = $1 WHERE id = $2 AND released_at IS NULL`

func (s *Store) Release(ctx context.Context, id order.ID, at time.Time) error {
	res, err := s.db.ExecContext(ctx, releaseOpen, at, id)
	if err != nil {
		return fmt.Errorf("releasing order %s: %w", id, err)
	}
	released, err := res.RowsAffected()
	if err != nil {
		return fmt.Errorf("releasing order %s: %w", id, err)
	}
	if released == 0 {
		return order.ErrNotOpen
	}
	return nil
}
```

Zero rows covers both "already released" and "no such order"; read back only when callers
branch on the difference.

**A use case spanning several port calls** first asks whether one port method can name the
unit (`PlaceWithReservation`); usually it can. When it cannot, the domain declares a small
port and the adapter runs the callback on a store bound to the transaction:

```go
type Transactions interface {
	Do(ctx context.Context, work func(Store) error) error
}
```

The adapter's methods take an unexported `querier` (`ExecContext`, `QueryContext`,
`QueryRowContext`), which `*sql.DB` and `*sql.Tx` both satisfy, so `Do` begins the
transaction, calls `work` with a store built on the `*sql.Tx`, and commits when `work`
returns nil. With gorm the adapter uses `db.Transaction(func(tx *gorm.DB) error { ... })`;
the port is the same.

Rows map to domain types in the adapter (`toOrder(row)`), through the domain constructor so
a corrupt row fails loudly. Migrations use the house's tool; the SQL lives where the house
keeps it (`go:embed`ded `.sql` files are common).

## HTTP handler

The handler holds the concrete `*order.Service`. It decodes a `json`-tagged DTO (domain types
carry no tags), builds the command through the domain constructor, calls the service and maps
the error in one function. Nothing else. From 1.27, `encoding/json/v2` (`json.UnmarshalRead`)
is the stricter choice: it rejects invalid UTF-8 and duplicate names; v1 keeps working.

```go
const maxBody = 1 << 20

type placeRequest struct {
	Customer string `json:"customer"`
	Cents    int64  `json:"cents"`
}

func (h *Handler) Register(mux *http.ServeMux) {
	mux.HandleFunc("POST /orders", h.place)
}

func (h *Handler) place(w http.ResponseWriter, r *http.Request) {
	var req placeRequest
	if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, maxBody)).Decode(&req); err != nil {
		http.Error(w, "malformed order", http.StatusBadRequest)
		return
	}
	cmd, err := order.NewPlace(order.CustomerID(req.Customer), req.Cents)
	if err != nil {
		h.writeError(w, r, err)
		return
	}
	id, err := h.orders.Place(r.Context(), cmd)
	if err != nil {
		h.writeError(w, r, err)
		return
	}
	h.writeJSON(w, r, http.StatusCreated, placeResponse{ID: string(id)})
}
```

## Errors to status, at the edge, once

```go
func statusOf(err error) int {
	var limit *order.LimitError
	switch {
	case errors.Is(err, order.ErrNotFound):
		return http.StatusNotFound
	case errors.Is(err, order.ErrInvalidAmount), errors.As(err, &limit):
		return http.StatusUnprocessableEntity
	default:
		return http.StatusInternalServerError
	}
}

func (h *Handler) writeError(w http.ResponseWriter, r *http.Request, err error) {
	status := statusOf(err)
	if status == http.StatusInternalServerError {
		h.log.ErrorContext(r.Context(), "handling order request", "err", err)
		http.Error(w, http.StatusText(status), status)
		return
	}
	http.Error(w, err.Error(), status)
}
```

Only the 500 branch logs, and it never echoes the error to the client. A second front-end over
the same service (an admin API) maps with its own function, built on the same `errors.Is/As`
set, so the two cannot diverge silently. A house error body (problem JSON, an envelope) replaces
`http.Error`; the shape stays.

The server sets `ReadHeaderTimeout` (gosec flags its absence) and shuts down on
`signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)` with `srv.Shutdown`, both in
`cmd/<app>/main.go`.

## Message consumer

An inbound adapter like the handler, in its own subpackage named for the house's broker or
`order/messaging`, named without stutter (`messaging.Consumer`, not `messaging.OrderConsumer`).

```go
func (c *Consumer) Handle(ctx context.Context, payload []byte) error {
	cmd, err := decodePlace(payload)
	if err != nil {
		c.log.WarnContext(ctx, "skipping undecodable order message", "err", err)
		return nil
	}
	_, err = c.orders.Place(ctx, cmd)
	var refused *order.RefusedError
	switch {
	case err == nil, errors.Is(err, order.ErrAlreadyPlaced):
		return nil
	case errors.As(err, &refused):
		c.log.InfoContext(ctx, "order refused", "reason", refused.Reason)
		return nil
	default:
		return fmt.Errorf("placing order from message: %w", err)
	}
}
```

- **Poison is never retried.** A payload that does not decode or fails the domain constructor
  is skipped and counted, or dead-lettered where the house has a DLQ.
- **Delivery is at least once**, so the use case is idempotent on a key the message carries
  (event ID as request ID), enforced by a unique constraint and `ON CONFLICT DO NOTHING` in the
  store; a redelivery is a no-op, not an error.
- **Classify once**: a refusal is an outcome (log, move on); anything else returns an error so
  the client library redelivers it, per its contract.
- **Publishing** never calls the broker inside a database transaction. Publish after the
  commit; where a lost event is not acceptable, write an outbox row in the same transaction and
  let a relay send it.
- Transaction scope per message or per batch is the house's call; follow its record.
