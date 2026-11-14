#!/bin/bash
set -e
mkdir -p src/main/java/com/acme/orders src/test/java/com/acme/orders
cat > pom.xml <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.acme</groupId>
  <artifactId>orders</artifactId>
  <version>0.1.0</version>
  <properties>
    <maven.compiler.release>25</maven.compiler.release>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.junit.jupiter</groupId>
      <artifactId>junit-jupiter</artifactId>
      <version>6.0.3</version>
      <scope>test</scope>
    </dependency>
    <dependency>
      <groupId>org.assertj</groupId>
      <artifactId>assertj-core</artifactId>
      <version>3.27.7</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>
XML
cat > src/main/java/com/acme/orders/Order.java <<'JAVA'
package com.acme.orders;

import java.util.List;
import java.util.Objects;

public record Order(String customerId, List<Long> lineCents) {
    public Order {
        Objects.requireNonNull(customerId);
        lineCents = List.copyOf(lineCents);
    }

    public long totalCents() {
        return lineCents.stream().mapToLong(Long::longValue).sum();
    }
}
JAVA
cat > src/main/java/com/acme/orders/OrderException.java <<'JAVA'
package com.acme.orders;

public class OrderException extends RuntimeException {
    public OrderException(String message) {
        super(message);
    }
}
JAVA
cat > src/main/java/com/acme/orders/EmptyOrderException.java <<'JAVA'
package com.acme.orders;

public class EmptyOrderException extends OrderException {
    public EmptyOrderException(String customerId) {
        super("order for " + customerId + " has no lines");
    }
}
JAVA
cat > src/main/java/com/acme/orders/OrderStore.java <<'JAVA'
package com.acme.orders;

public interface OrderStore {
    void save(Order order);
}
JAVA
cat > src/main/java/com/acme/orders/PlaceOrderService.java <<'JAVA'
package com.acme.orders;

public class PlaceOrderService {
    private final OrderStore store;

    public PlaceOrderService(OrderStore store) {
        this.store = store;
    }

    public void place(Order order) {
        if (order.lineCents().isEmpty()) {
            throw new EmptyOrderException(order.customerId());
        }
        store.save(order);
    }
}
JAVA
cat > src/test/java/com/acme/orders/PlaceOrderServiceTest.java <<'JAVA'
package com.acme.orders;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.catchThrowable;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class PlaceOrderServiceTest {
    private final List<Order> saved = new ArrayList<>();
    private final PlaceOrderService service = new PlaceOrderService(saved::add);

    @Test
    void givenOrderWithoutLines_whenPlace_thenRefusedAndNothingSaved() {
        var order = new Order("c-1", List.of());

        var thrown = catchThrowable(() -> service.place(order));

        assertThat(thrown).isInstanceOf(EmptyOrderException.class);
        assertThat(saved).isEmpty();
    }
}
JAVA
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "order service with empty-order check"
