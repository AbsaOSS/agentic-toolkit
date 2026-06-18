# PR Review Output Examples

Use these as a template for formatting your review. The goal is to be useful, not thorough — a short focused review is better than a long one that buries the signal.

---

## Example 1: Clean PR (LGTM)

```markdown
## Applied sections: Standard

Files changed: `src/utils/date_utils.py`, `tests/utils/test_date_utils.py`

**Blocker**
_None._

**Important**
_None._

**Nit**
- `get_business_days` uses an O(n) loop. A week-math formula is O(1) and simpler — worth
  switching if this is called on large date ranges. Not blocking.

Overall: LGTM. Clean utility, good test coverage, no dependencies added.
```

---

## Example 2: Multi-section review (API + CI/CD)

```markdown
## Applied sections: Standard · API contracts · CI/CD

**Blocker**

1. `GET /users/{id}` response field rename — breaking contract  
   - **What**: `user_id` → `userId` changes the JSON wire format with no backward-compat alias.  
   - **Why**: Every existing caller receives `null` for `user_id` the moment this deploys.  
   - **How to fix**: Use `Field(alias="user_id")` to keep the old wire name, or version the endpoint.

2. Unit tests commented out in CI  
   - **What**: `pytest` step disabled in `.github/workflows/ci.yml` (line 28).  
   - **Why**: Coverage gate bypassed — broken code can reach staging undetected.  
   - **How to fix**: Fix the specific flaky tests; don't disable the gate.

**Important**

3. Deploy trigger widened to all pushes  
   - **What**: `if: github.ref == 'refs/heads/develop'` changed to `github.event_name == 'push'`.  
   - **Why**: Staging now deploys on `main` pushes too, breaking the expected promotion flow.  
   - **How to fix**: Restore the branch-scoped guard.

**Nit**
_None._
```

---

## Example 3: Elevated risk PR (auth/security change)

```markdown
## Applied sections: Standard · Elevated risk · API contracts

**Blocker**

1. Wildcard IAM policy (`Action: "*"`, `Resource: "*"`)  
   - **What**: `lambda_data_access` policy grants unrestricted access to the entire AWS account.  
   - **Why**: A compromised Lambda can exfiltrate data, destroy resources, or escalate privileges.  
   - **How to fix**: Scope to the specific actions and resource ARNs the function actually needs.

**Important**

2. Hardcoded account ID as variable default  
   - **What**: `variable "account_id" { default = "123456789012" }` — silently targets a single account.  
   - **Why**: Any caller that forgets to override will deploy against the wrong account.  
   - **How to fix**: Remove the default; use `data "aws_caller_identity" "current" {}` instead.

**Nit**
- `Sid = "FullDataAccess"` is misleading — once scoped, rename to reflect actual access.
```

---

## Formatting rules

- Reference file + line number where possible: `src/api/router.py:42`
- Quote the actual code in a fenced block when it helps clarity
- If a section has no findings, write `_None._` explicitly — it shows you checked
- Keep the "How to fix" minimal: a code snippet or a pattern name is enough; don't write an essay
- Omit sections entirely if they don't apply to this PR
