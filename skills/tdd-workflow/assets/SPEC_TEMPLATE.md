# <Component/Feature Name>

## Purpose
One paragraph: what this component does, why it exists, and the public interface it provides. Be specific about the inputs it accepts and outcomes it produces.

## Scenarios

Describe the happy path and key failure modes. Each row should have concrete inputs and expected outputs that a developer could test against.

| # | Name | Intent | Input | Expected Output |
|---|------|--------|-------|-----------------|
| 1 | name | clear one-line goal | specific input values | specific result or error |
| 2 | ... | ... | ... | ... |

**Examples:**
- ✅ GOOD: "approve valid card" | "card=4111111111111111, amount=100.00" | "approved + transaction_id"
- ❌ VAGUE: "handle cards" | "card data" | "works or fails"

## Edge Cases

List known boundary conditions and failure modes. Think systematically:
- **Input validation:** What happens with empty, null, negative, zero, or very large values?
- **Boundary conditions:** What's the smallest positive value? Largest supported? Off-by-one boundaries?
- **Format variations:** Spaces, dashes, case sensitivity, trailing zeros?
- **State transitions:** Can operation B happen before operation A? What's the valid sequence?
- **Precondition violations:** What if a required precondition doesn't exist?

Example:
```
- Card normalization: spaces and dashes are stripped before Luhn validation
- Zero and negative amounts: rejected with validation error
- Refund ceilings: cannot refund more than the remaining approved balance
- Unknown transactions: refund request for non-existent tx returns error
```

## Out of Scope

What this component does NOT handle (prevents scope creep and clarifies stopping points):

Example:
```
- PCI-compliant storage or encryption
- Real payment gateway integration
- Chargebacks or payment disputes
- Card brand detection (only Luhn validation)
- Multi-currency support
```

## Open Questions

Unresolved design decisions needing input before implementation. Marking these now prevents rework later:

Example:
```
- Should errors be exceptions, result objects, or status codes?
- Should amounts be Decimal, integer cents, or language-native money type?
- Are refunds idempotent per refund ID or simply additive?
```

## Design Decisions (Optional but Helpful)

Once you've reviewed this SPEC with the user and they've approved your test plan, record key design choices here before implementation:

```
- Error handling: Choose one → _____
- Amount representation: Choose one → _____
- [Other decision] → _____
```

This prevents rework when implementing.
