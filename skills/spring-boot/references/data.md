<!-- Adapted from piomin/claude-ai-spring-boot (Apache-2.0); modified for delivery-doctrine. See THIRD_PARTY_NOTICES.md. -->

# Data Access - Spring Data JPA

Read when the slice touches persistence. The persistence adapter lives in
`<feature>.persistence` and implements the domain's port; JPA entities are adapter types mapped
to and from the aggregate (`delivery-doctrine:java-domain`). Examples carry ✅/❌ labels to
teach; delivered code carries none.

Spring Boot 4 ships Spring Data 2025.1 (Spring Data JPA 4) on Hibernate 7 and Jakarta Persistence 3.2. `@EntityScan` moved to `org.springframework.boot.persistence.autoconfigure.EntityScan`, `hibernate-jpamodelgen` is replaced by `hibernate-processor`, and `spring.dao.exceptiontranslation.enabled` is now `spring.persistence.exceptiontranslation.enabled`. Set `spring.jpa.open-in-view=false`.

## Entity, repository, adapter
```java
@Entity
@Table(name = "orders", indexes = @Index(name = "idx_orders_customer", columnList = "customer_id"))
class OrderEntity {
    @Id
    private UUID id;
    @Column(name = "customer_id", nullable = false)
    private UUID customerId;
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private OrderStatus status;
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderLineEntity> lines = new ArrayList<>();
    @Version
    private long version;

    protected OrderEntity() {}

    static OrderEntity from(Order order) { ... }

    Order toDomain() { ... }
}

interface OrderJpaRepository extends JpaRepository<OrderEntity, UUID> {
    @EntityGraph(attributePaths = "lines")
    Optional<OrderEntity> findWithLinesById(UUID id);

    @Modifying
    @Query("""
        UPDATE OrderEntity o SET o.status = com.acme.orders.OrderStatus.RELEASED
        WHERE o.id = :id AND o.status = com.acme.orders.OrderStatus.PLACED""")
    int releaseIfPlaced(@Param("id") UUID id);
}

class JpaOrderStore implements OrderStore {
    private final OrderJpaRepository repository;

    JpaOrderStore(OrderJpaRepository repository) {
        this.repository = repository;
    }

    @Override
    @Transactional
    public void place(Order order) {
        repository.save(OrderEntity.from(order));
    }

    @Override
    @Transactional(readOnly = true)
    public Optional<Order> byId(OrderId id) {
        return repository.findWithLinesById(id.value()).map(OrderEntity::toDomain);
    }

    @Override
    @Transactional
    public boolean release(OrderId id) {
        return repository.releaseIfPlaced(id.value()) == 1;
    }
}
```
- The entity has no public setters and no business rules; the aggregate keeps the invariants,
  the entity only maps. A protected no-arg constructor satisfies JPA. If the house maps JPA
  straight onto the aggregate, follow it and say so in the slice.
- IDs: an application-assigned `UUID` lets the domain create an `OrderId` before the insert;
  `@GeneratedValue(strategy = IDENTITY)` where the house uses database keys.
- `@Version` gives optimistic locking: a stale update throws
  `ObjectOptimisticLockingFailureException`, mapped to 409 at the edge.
- `@Enumerated(EnumType.STRING)`, never the ordinal: reordering constants corrupts data.
- A conditional `UPDATE … WHERE` (`releaseIfPlaced`) enforces a lifecycle rule against a
  read-update-persist race; it returns the row count, and 0 means the rule refused. The domain
  method mirrors it and one test pins the two together (`java-domain`).
- Audit columns: `@CreatedDate`/`@LastModifiedDate` (and `@CreatedBy` with an `AuditorAware` bean)
  under `@EntityListeners(AuditingEntityListener.class)` and `@EnableJpaAuditing` on a configuration class.
- Read models: a record projection (`List<OrderSummary> findByCustomerId(UUID id)` with
  `record OrderSummary(UUID id, String status)`), or a dynamic one (`<T> List<T> findByCustomerId(UUID id, Class<T> type)`),
  so a list screen never loads whole aggregates.
- Specifications for optional criteria: since Spring Data JPA 4, `Specification.where(...)` rejects `null`; start from `Specification.unrestricted()` or combine with `Specification.allOf(...)` when the first criterion may be absent. A specification whose predicate is `null` is still allowed.

## Transactions
- **One port call is one transaction**, on the adapter method. A use case spanning several port
  calls depends on the domain's `Transactions` port; its adapter is
  `template.execute(status -> work.get())` on a `TransactionTemplate` (`java-domain`).
- **Proxies apply only from outside.** `@Transactional` on a private method, or a call from the
  same class, runs without the transaction.
- **No remote call inside a transaction**: it holds the connection for the whole call, and a commit
  that fails after the call succeeded leaves the remote side changed (a payment for an order that
  does not exist). Call it after the commit, or write an outbox row in the transaction and let a
  relay make the call.
- **`REQUIRES_NEW`** for a record that must survive the caller's rollback (an audit entry of the
  attempt); it takes a second connection, so never under open-in-view or in a loop.
- **After-commit side effects** through `@TransactionalEventListener` (`AFTER_COMMIT`, the default
  phase): a rolled-back change publishes nothing, and a failed send cannot undo the commit. The
  listener's exception still reaches the caller after the commit; a best-effort notification
  catches and logs it. The listener is not invoked when no transaction is running unless it sets
  `fallbackExecution = true`.

## Queries
- **N+1**: one query per row of a list. Fix with a fetch join (`JOIN FETCH`; Hibernate 6+ removes
  the duplicate roots without `DISTINCT`), `@EntityGraph`, or `@BatchSize` on the association.
- **Fetch join plus paging** of a collection makes Hibernate page in memory (it logs a warning):
  page the root IDs first, then fetch those roots with their collections.
- **Page or stream** anything that grows; a `findAll()` on a growing table is a finding.
- **Native queries** for what JPQL cannot say, always with parameters (`:since`), never concatenation.
- Turn `org.hibernate.SQL` to `DEBUG` while chasing a query, and back off before commit.

## Migrations (Flyway)
In Spring Boot 4, Flyway auto-configuration needs `spring-boot-starter-flyway` (plus the database module, e.g. `flyway-database-postgresql`); `flyway-core` alone no longer triggers it.

```sql
CREATE TABLE orders (
    id          UUID PRIMARY KEY,
    customer_id UUID        NOT NULL,
    status      VARCHAR(20) NOT NULL,
    version     BIGINT      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_orders_customer ON orders (customer_id);
```
- `V<n>__<what>.sql`; a merged migration is never edited, only followed by a new one.
- `spring.jpa.hibernate.ddl-auto=validate` (or `none`): the schema comes from migrations, never
  from Hibernate.
- A change that existing rows or the previous release cannot read ships expand then contract: add
  the new column and write both, backfill, switch reads, drop the old one in a later release.
