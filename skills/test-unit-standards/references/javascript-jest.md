# JavaScript / TypeScript + Jest — Language Reference

Loaded by `test-unit-standards`, `test-unit-write`, and `test-unit-review` when JavaScript or
TypeScript is detected. Apply these conventions on top of the language-agnostic rules in
`test-unit-standards/SKILL.md`.

---

## Test naming

Use `describe` to group tests by unit under test, and `it` / `test` for individual cases.
Each case name must state the condition and expected outcome.

```typescript
// ✅
describe('applyDiscount', () => {
  it('returns 20% off when tier is gold', () => { ... });
  it('returns 10% off when tier is silver', () => { ... });
  it('returns full price when tier is null', () => { ... });
  it('throws RangeError when price is negative', () => { ... });
  it('returns 0 when price is 0', () => { ... });
});

// ❌ — vague, no condition or expected outcome
describe('discount', () => {
  it('works', () => { ... });
  it('test1', () => { ... });
  it('handles edge cases', () => { ... });
});
```

Flat `test('unitName when condition returns expected', ...)` is also acceptable when `describe`
nesting would be unnecessary.

---

## Private member convention

Modern JavaScript / TypeScript uses `#` for truly private fields (hard private). Older codebases
use `_` or `__` by convention (soft private). Tests must not access either.

```typescript
// ✅ — test through the public API
it('throws UnauthorizedError for an expired token', () => {
  expect(() => validator.validate(expiredToken)).toThrow(UnauthorizedError);
});

// ❌ — accessing a hard-private field via type cast
it('extracts the sub claim from the payload', () => {
  const result = (validator as any)['#decode'](token);   // private — not allowed
  expect(result.sub).toBe('user123');
});

// ❌ — accessing a soft-private field
it('cache is populated after validation', () => {
  validator.validate(validToken);
  expect((validator as any)._cache).toContain('user123');  // private — not allowed
});
```

---

## Test file placement

```
src/
├── services/
│   ├── payment.service.ts
│   └── payment.service.test.ts    ← co-located, same directory
```

or a mirrored `__tests__` directory:

```
src/
└── services/
    └── payment.service.ts
__tests__/
└── services/
    └── payment.service.test.ts
```

Suffix: `.test.ts` or `.spec.ts`. One test file per source module.

---

## Setup and teardown

Use `beforeEach` / `afterEach` for per-test setup. Always call `jest.clearAllMocks()` in
`beforeEach` to prevent mock state from leaking between tests.

```typescript
// ✅
let mockCharge: jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  mockCharge = jest.fn().mockResolvedValue({ id: 'ch_123', status: 'succeeded' });
});

// ❌ — mock created once at module scope; state accumulates across tests
const mockCharge = jest.fn();
```

---

## Mocking modules

Use `jest.mock(...)` at the top of the file — Jest hoists it before `import` statements.

```typescript
// ✅ — module mock hoisted automatically
jest.mock('../httpClient');
import { httpClient } from '../httpClient';

const mockPost = httpClient.post as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  mockPost.mockResolvedValue({ data: { id: 'order_1' } });
});

it('returns the created order id', async () => {
  const result = await orderService.place('u1', 'SKU-1', 2);
  expect(result.id).toBe('order_1');
});

// ❌ — manual mock defined inside a test body; does not intercept the module import
it('returns the created order id', async () => {
  const mockPost = jest.fn().mockResolvedValue({ data: { id: 'order_1' } });
  // ... mockPost is never injected into the module
});
```

---

## Assertion style

Use specific Jest matchers. Avoid `toBeTruthy()` or `toBeDefined()` when an exact value is known.

```typescript
// ✅
expect(result).toEqual({ id: 'order_1', status: 'placed' });
expect(mockSend).toHaveBeenCalledWith('u1', expect.stringContaining('SKU-1'));
expect(mockSend).toHaveBeenCalledTimes(1);
expect(() => service.placeOrder('u1', 'SKU-X', -1)).toThrow(RangeError);
await expect(service.placeOrder('u1', '', 1)).rejects.toThrow('sku is required');

// ❌ — too weak
expect(result).toBeTruthy();
expect(result).toBeDefined();
expect(mockSend.mock.calls.length).not.toBe(0);   // use toHaveBeenCalled() instead
expect(result).not.toBeNull();                     // use toEqual with the actual value
```

---

## Exception and async error testing

```typescript
// ✅ — synchronous throw
expect(() => applyDiscount(-1, 'gold')).toThrow(RangeError);
expect(() => applyDiscount(-1, 'gold')).toThrow('price must be non-negative');

// ✅ — async rejection
await expect(service.placeOrder('u1', 'SKU-X', 100))
  .rejects.toThrow(InsufficientStockError);

// ❌ — silent failure on async errors
it('throws on insufficient stock', () => {         // missing async/await
  expect(service.placeOrder('u1', 'SKU-X', 100)).rejects.toThrow(...);
});
```

---

## Parametrised tests

Use `test.each` (table form) for multiple input variations of the same logic.

```typescript
// ✅
test.each([
  ['gold',   100, 80],
  ['silver', 100, 90],
  [null,     100, 100],
  ['gold',   0,   0],     // boundary
] as const)('applyDiscount(%s, %i) returns %i', (tier, price, expected) => {
  expect(applyDiscount(price, tier)).toBe(expected);
});

// ❌ — four separate test functions testing the same logic
test('applyDiscount returns 80 for gold',   () => expect(applyDiscount(100, 'gold')).toBe(80));
test('applyDiscount returns 90 for silver', () => expect(applyDiscount(100, 'silver')).toBe(90));
test('applyDiscount returns 100 for null',  () => expect(applyDiscount(100, null)).toBe(100));
test('applyDiscount returns 0 at boundary', () => expect(applyDiscount(0, 'gold')).toBe(0));
```
