# BankAccount

## Purpose
A simple bank account that supports deposit, withdrawal, and balance inquiry. Used as a TDD fixture to verify that generated tests interact only with the public interface.

## Scenarios

| # | Name | Intent | Input | Expected Output |
|---|------|--------|-------|-----------------|
| 1 | deposit increases balance | depositing a positive amount | account(0), deposit(100) | balance == 100 |
| 2 | withdraw decreases balance | withdrawing less than balance | account(200), withdraw(50) | balance == 150 |
| 3 | withdraw insufficient funds | withdrawing more than balance | account(50), withdraw(100) | raises InsufficientFundsError |
| 4 | deposit zero | depositing zero is a no-op | account(100), deposit(0) | balance == 100 |
| 5 | withdraw exact balance | draining account to zero | account(100), withdraw(100) | balance == 0 |
| 6 | negative deposit rejected | negative deposits are invalid | account(100), deposit(-10) | raises ValueError |

## Edge Cases
- Concurrent deposits/withdrawals are out of scope.
- Floating-point precision: amounts are assumed to be integers for this scenario.

## Out of Scope
- Interest accrual
- Transaction history
- Multi-currency support

## Open Questions
_None._ Design decisions resolved: `withdraw(0)` is allowed and treated as a no-op (balance unchanged), consistent with how `deposit(0)` behaves.
