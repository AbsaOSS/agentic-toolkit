---
name: test-mocking-patterns
description: >
  Guides selection and implementation of test doubles (mock, stub, spy, fake, dummy) in unit
  tests. Activate when deciding which double type to use, implementing a specific double,
  debugging a non-working mock or stub, or choosing a patching strategy (where to patch,
  scope, partial mocking, resetting between tests).
  Triggers on: "should I use a spy or mock", "what test double should I use", "how do I mock
  this", "how to stub HTTP calls", "fake vs mock vs stub", "how to patch", "where should I
  patch", "mock not being called", "my mock isn't working", "how to spy on a method",
  "stub vs mock", "when to use a fake", "how to mock a class method", "how to mock an
  environment variable", "how do I verify a method was called".
  Does NOT trigger for: writing full test suites (use test-unit-write), reviewing test files
  against standards (use test-unit-review), managing test data and fixture builders
  (use test-data-management), debugging test errors (TypeError, KeyError).
  Pairs with test-unit-write and test-unit-review.
license: Proprietary
compatibility: GitHub Copilot
---

# Test Mocking Patterns

## Step 1 — Classify the dependency

Determine what kind of interaction the test needs to control or verify:

| Situation | Recommended double |
|---|---|
| Dependency returns a value; no need to verify it was called | **Stub** |
| Dependency is called for its side effect; verify it was called | **Mock** |
| Need to verify the call AND use the real return value | **Spy** |
| Stateful in-process replacement of an interface | **Fake** |
| Argument must satisfy a type signature but is never used | **Dummy** |

> Prefer stubs over mocks when possible — stubs make fewer assumptions about how the unit under test works internally, keeping tests less brittle.

## Step 2 — Implement by language

### Python — pytest-mock / unittest.mock

| Double | How |
|---|---|
| **Stub** | `mocker.patch('module.Class.method', return_value=...)` |
| **Mock** | `mocker.patch('module.Class.method')` → assert with `.assert_called_once_with(...)` |
| **Spy** | `mocker.spy(obj, 'method_name')` — calls through, records calls |
| **Fake** | Implement a minimal in-memory class satisfying the same interface |
| **Dummy** | `MagicMock()` passed in but never called |

#### Where to patch (Python)

Patch the name **as it is imported in the module under test**, not where the object is defined.

```python
# ✅ — patch where 'requests' is imported inside myapp.services.user_service
mocker.patch("myapp.services.user_service.requests.get", return_value=stub_response)

# ❌ — patching the source module has no effect on the module under test
mocker.patch("requests.get", return_value=stub_response)
```

#### Scope and cleanup (Python)

`mocker` fixtures from `pytest-mock` are automatically cleaned up after each test.
For `unittest.mock.patch`, use `with patch(...)` or the `@patch` decorator — both clean up on exit.

```python
# ✅ — mocker fixture (auto cleanup)
def test_something(mocker):
    mocker.patch("myapp.service.Client.send", return_value={"ok": True})
    ...

# ✅ — context manager (explicit cleanup)
def test_something():
    with patch("myapp.service.Client.send", return_value={"ok": True}):
        ...

# ❌ — manual patch without cleanup leaks into subsequent tests
patcher = patch("myapp.service.Client.send")
mock_send = patcher.start()
# missing patcher.stop()
```

#### Assertions on mocks (Python)

```python
# ✅ — specific argument assertions
mock_send.assert_called_once_with("user@example.com", subject="Welcome")
mock_send.assert_called_with(ANY, subject=ANY)   # use ANY for irrelevant args

# ❌ — always True; proves nothing
assert mock_send.called is not None
assert mock_send.call_count >= 0
```

---

### JavaScript / TypeScript — Jest

| Double | How |
|---|---|
| **Stub** | `jest.fn().mockReturnValue(...)` or `jest.spyOn(obj, 'method').mockReturnValue(...)` |
| **Mock** | `jest.mock('../path/to/module')` — full module replacement |
| **Spy** | `jest.spyOn(obj, 'method')` — calls through by default, records calls |
| **Fake** | Implement a class satisfying the interface |

#### Module mock (Jest)

```typescript
// ✅ — jest.mock is hoisted before imports
jest.mock('../httpClient');
import { httpClient } from '../httpClient';

const mockPost = httpClient.post as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  mockPost.mockResolvedValue({ data: { id: 'order_1' } });
});

// ❌ — inline mock does not intercept the already-imported module
it('places order', async () => {
  const mockPost = jest.fn().mockResolvedValue(...);   // never injected
});
```

#### Cleanup (Jest)

Call `jest.clearAllMocks()` in `beforeEach` to reset call records. Use `jest.resetAllMocks()`
to also remove implementations. Use `jest.restoreAllMocks()` to restore `jest.spyOn` originals.

```typescript
beforeEach(() => {
  jest.clearAllMocks();   // reset call counts and recorded calls
});
```

#### Assertions (Jest)

```typescript
// ✅
expect(mockSend).toHaveBeenCalledWith('user@example.com', expect.objectContaining({ subject: 'Welcome' }));
expect(mockSend).toHaveBeenCalledTimes(1);

// ❌ — always truthy; proves nothing
expect(mockSend.mock.calls.length).not.toBe(0);
```

---

### Scala — mockito-scala

```scala
import org.mockito.MockitoSugar._

// Stub
val repo = mock[UserRepository]
when(repo.findById(any[UserId])).thenReturn(Some(testUser))

// Mock (verify call)
val notifier = mock[Notifier]
service.process(userId)
verify(notifier).send(eqTo(userId), any[String])

// Spy (calls through, records)
val realCache = new InMemoryCache()
val spyCache  = spy(realCache)
service.process(userId)
verify(spyCache).get(eqTo(userId))

// Fake
class InMemoryUserRepository extends UserRepository {
  private val store = mutable.Map.empty[UserId, User]
  override def findById(id: UserId): Option[User] = store.get(id)
  override def save(user: User): Unit = store.update(user.id, user)
}
```

Reset mocks between tests with `reset(mock)` in `beforeEach`, or declare mocks inside the test
body so they are function-scoped.

## Step 3 — Verify the double is wired correctly

Common mistakes to check regardless of language:

| Symptom | Likely cause | Fix |
|---|---|---|
| Mock method never called but test passes | Mock not injected into the unit under test | Confirm the unit receives the mock, not the real object |
| `assert_called` fails but call is visible in logs | Patching the wrong namespace (Python) | Patch where the name is imported, not defined |
| Mock state bleeds between tests | No cleanup between tests | Use `clearAllMocks` / `mocker` fixture / reset |
| Test is brittle — breaks on unrelated internal changes | Over-specified arguments in assertion | Use matchers (`any()`, `expect.any(String)`) for args the test doesn't depend on |
| Test directly calls a private/internal method | Private methods are implementation detail | Test private logic indirectly through the public interface — verify the side effect on the injected collaborator instead |
| Stub returns wrong type | `return_value` is a raw dict but code calls `.json()` on it | Use `MagicMock(json=lambda: {...})` or return a correctly-shaped object |

## Mocking environment variables (Python)

When a module reads `os.environ` at call time, use `mocker.patch.dict` or `monkeypatch.setenv` —
both are automatically cleaned up after the test:

```python
# ✅ — patch.dict approach (pytest-mock)
def test_uses_promotions_url(mocker):
    mocker.patch.dict("os.environ", {"PROMOTIONS_API_URL": "http://test-promos"})
    result = service.fetch_promotions()
    assert result is not None

# ✅ — monkeypatch approach (built-in pytest fixture)
def test_uses_promotions_url(monkeypatch):
    monkeypatch.setenv("PROMOTIONS_API_URL", "http://test-promos")
    result = service.fetch_promotions()
    assert result is not None

# ❌ — direct mutation leaks state into subsequent tests
os.environ["PROMOTIONS_API_URL"] = "http://test-promos"
```

> Prefer `monkeypatch.setenv` for single variables; `mocker.patch.dict("os.environ", {...})` when
> setting multiple keys at once.

## Routing

- Writing a full test suite (generating all test methods) → use **test-unit-write**
- Reviewing a test file for standards violations → use **test-unit-review**
- Managing test data setup, factories, parametrisation → use **test-data-management**
