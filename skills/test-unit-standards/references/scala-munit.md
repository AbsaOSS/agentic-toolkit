# Scala + MUnit — Language Reference

Loaded by `test-unit-standards`, `test-unit-write`, and `test-unit-review` when Scala is detected.
Apply these conventions on top of the language-agnostic rules in `test-unit-standards/SKILL.md`.

---

## Test naming

MUnit uses string literals as test names. Names must state the unit, condition, and expected outcome
in plain English. Prefer the pattern: `"<unit> <condition> returns/throws/emits <expected>"`.

```scala
// ✅
test("applyDiscount with gold tier returns 20% off") { ... }
test("applyDiscount with negative price throws IllegalArgumentException") { ... }
test("applyDiscount with zero price returns 0") { ... }
test("placeOrder when stock is insufficient throws InsufficientStockException") { ... }

// ❌ — vague, no condition or expected outcome
test("discount") { ... }
test("it works") { ... }
test("test1") { ... }
```

For grouping, use a dedicated `Suite` class per unit under test:

```scala
class ApplyDiscountSuite extends FunSuite { ... }
class OrderServiceSuite extends FunSuite { ... }
```

---

## Private member convention

Scala marks private members with `private` or `private[package]` visibility modifiers. Tests must
not use reflection or other mechanisms to access them.

```scala
// ✅ — test through the public API
test("validate with expired token throws UnauthorizedException") {
  intercept[UnauthorizedException] {
    validator.validate(expiredToken)
  }
}

// ❌ — accessing private method via reflection
test("decode extracts sub claim") {
  val method = validator.getClass.getDeclaredMethod("decode", classOf[String])
  method.setAccessible(true)                   // private — not allowed
  val result = method.invoke(validator, token)
  assertEquals(result.asInstanceOf[Map[String, String]]("sub"), "user123")
}
```

---

## Test file placement

```
src/
└── main/
    └── scala/
        └── com/example/services/
            └── OrderService.scala
src/
└── test/
    └── scala/
        └── com/example/services/
            └── OrderServiceSuite.scala   ← mirrors main/ path, suffixed with Suite
```

One `Suite` class per source class. Place shared helpers in a `TestSupport` trait or object.

---

## Fixtures and setup

MUnit provides `beforeEach` / `afterEach` hooks and `fixture` helpers for resource management.

```scala
// ✅ — FunFixtures for managed resources
val stubGateway: Fixture[PaymentGateway] = FunFixture(
  setup    = _ => StubPaymentGateway(),
  teardown = _ => ()
)

// ✅ — beforeEach for simple resets
var mockRepo: MockInventoryRepo = _

override def beforeEach(context: BeforeEach): Unit = {
  mockRepo = new MockInventoryRepo()
}

// ❌ — shared mutable val at class level, never reset between tests
val mockRepo = new MockInventoryRepo()  // state accumulates — tests become order-dependent
```

---

## Assertion style

Use MUnit's `assertEquals`, `assertThrows`, and `interceptMessage` for specific assertions.

```scala
// ✅
assertEquals(applyDiscount(100.0, Tier.Gold), 80.0)
assertEquals(result, Order(userId = "u1", sku = "SKU-1", status = "placed"))

assertThrows[InsufficientStockException] {
  orderService.placeOrder("u1", "SKU-X", 100)
}

// ✅ — check exception message
val ex = interceptMessage[IllegalArgumentException]("quantity must be positive") {
  orderService.placeOrder("u1", "SKU-1", 0)
}

// ❌ — too weak
assert(result != null)
assert(result.isInstanceOf[Order])   // proves type, not value
assert(called)                        // truthy check — use specific verify instead
```

---

## Mocking (mockito-scala)

```scala
import org.mockito.MockitoSugar._

// ✅ — stub a return value
val repo = mock[InventoryRepository]
when(repo.getStock("SKU-1")).thenReturn(10)

// ✅ — verify a call
verify(repo).reserve("SKU-1", 2)

// ✅ — argument matchers for irrelevant args
when(repo.getStock(any[String])).thenReturn(5)

// ❌ — over-specifying unrelated arguments makes the test brittle
verify(repo).reserve(eqTo("SKU-1"), eqTo(2))  // fine when both matter
verify(repo).reserve(any(), eqTo(2))           // ✅ when only qty matters
```

Reset mocks between tests using `reset(mock)` in `beforeEach`, or declare mocks inside the test
body / fixture so they are scoped per test.

---

## Data-driven tests

Use `List(...).foreach` or `FunSuite`'s table helpers for multiple input variations.

```scala
// ✅
List(
  ("gold",   100.0, 80.0),
  ("silver", 100.0, 90.0),
  ("bronze", 100.0, 95.0),
  ("gold",   0.0,   0.0),   // boundary
).foreach { case (tier, price, expected) =>
  test(s"applyDiscount $tier $price returns $expected") {
    assertEquals(applyDiscount(price, Tier.withName(tier)), expected)
  }
}

// ❌ — separate test per variation
test("applyDiscount gold 100 returns 80")   { assertEquals(applyDiscount(100.0, Tier.Gold),   80.0) }
test("applyDiscount silver 100 returns 90") { assertEquals(applyDiscount(100.0, Tier.Silver), 90.0) }
```

---

## Async tests

MUnit supports `Future`-returning tests natively. Always return the `Future` from the test body.

```scala
// ✅
test("placeOrder resolves with order id") {
  orderService.placeOrder("u1", "SKU-1", 2).map { order =>
    assertEquals(order.id.isEmpty, false)
  }
}

// ❌ — fire-and-forget; test passes before the Future completes
test("placeOrder resolves with order id") {
  orderService.placeOrder("u1", "SKU-1", 2)   // Future not returned — assertion never runs
}
```
