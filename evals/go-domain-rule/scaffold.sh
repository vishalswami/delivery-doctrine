#!/bin/bash
set -e
mkdir -p internal/order
cat > go.mod <<'GO'
module example.com/shop

go 1.26
GO
cat > internal/order/order.go <<'GO'
package order

import (
	"context"
	"errors"
)

var ErrEmptyOrder = errors.New("order has no lines")

type CustomerID string

type Line struct {
	SKU   string
	Cents int64
}

type Order struct {
	Customer CustomerID
	Lines    []Line
}

func (o Order) TotalCents() int64 {
	var total int64
	for _, l := range o.Lines {
		total += l.Cents
	}
	return total
}

type Store interface {
	Save(ctx context.Context, o Order) error
}

type Service struct {
	store Store
}

func NewService(store Store) *Service {
	return &Service{store: store}
}

func (s *Service) Place(ctx context.Context, o Order) error {
	if len(o.Lines) == 0 {
		return ErrEmptyOrder
	}
	return s.store.Save(ctx, o)
}
GO
cat > internal/order/order_test.go <<'GO'
package order_test

import (
	"context"
	"errors"
	"testing"

	"example.com/shop/internal/order"
)

type fakeStore struct {
	saved []order.Order
}

func (f *fakeStore) Save(_ context.Context, o order.Order) error {
	f.saved = append(f.saved, o)
	return nil
}

func TestPlace(t *testing.T) {
	t.Parallel()
	t.Run("given an order without lines when placed then refused", func(t *testing.T) {
		t.Parallel()
		store := &fakeStore{}
		service := order.NewService(store)

		err := service.Place(context.Background(), order.Order{Customer: "c-1"})

		if !errors.Is(err, order.ErrEmptyOrder) {
			t.Fatalf("got %v, want ErrEmptyOrder", err)
		}
	})
}
GO
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "order service with empty-order check"
