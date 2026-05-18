# Security Anti-Patterns Reference

Quick reference of patterns to actively look for during PR review. Not exhaustive — use these as prompts when reading code, not as a checklist to run down mechanically.

---

## Credentials & Secrets

| Pattern | What to look for |
|---|---|
| Hardcoded creds | String literals matching `AKIA`, `sk-`, `ghp_`, `-----BEGIN`, passwords/tokens in assignments |
| Secret in env block | `env:` in CI with literal values instead of `${{ secrets.X }}` |
| Secret in log | `print(token)`, `logger.info(password)`, `console.log(apiKey)` |
| Secret in URL | `https://user:pass@host`, connection strings with embedded credentials |
| `.env` committed | `.env`, `.env.local`, `.env.production` added to the diff |

## Injection

| Pattern | What to look for |
|---|---|
| SQL injection | String-formatted queries: `f"SELECT * FROM {table}"`, `"WHERE id=" + user_input` |
| Command injection | `os.system(input)`, `subprocess.run(f"cmd {input}", shell=True)`, `exec(user_data)` |
| Template injection | User-controlled strings passed to Jinja2/Mustache/eval without escaping |
| Path traversal | `open(base_dir + user_path)` without `Path.resolve()` / `realpath()` check |

## Auth & Access Control

| Pattern | What to look for |
|---|---|
| Missing auth check | Endpoint added without `@require_auth`, `@login_required`, or middleware check |
| Broken object-level auth | Fetching a resource by ID without verifying the caller owns it |
| Privilege escalation | Role/permission assigned from user-supplied input without validation |
| JWT `alg: none` | JWT verification that accepts unsigned tokens |
| Wildcard IAM | `Action: "*"` or `Resource: "*"` in IAM policies |

## Cryptography

| Pattern | What to look for |
|---|---|
| Weak hash | `md5(password)`, `sha1(secret)` — use bcrypt/argon2 for passwords |
| Static IV/nonce | Same IV reused across encryptions |
| Insecure random | `random.random()` / `Math.random()` for security tokens — use `secrets` / `crypto.randomBytes` |

## Input Validation

| Pattern | What to look for |
|---|---|
| Missing size limit | File upload or request body accepted without size cap |
| Unvalidated redirect | `redirect(request.args['next'])` without allow-list check |
| XXE | XML parser without `resolve_entities=False` / external entity disabled |
| SSRF | HTTP client called with user-controlled URL without allow-list |

## Data Handling

| Pattern | What to look for |
|---|---|
| PII in logs | Email, phone, card number, SSN in log statements |
| PII in URL | Sensitive identifiers in query params (captured by access logs, proxies, browsers) |
| Insecure deserialization | `pickle.loads(user_data)`, `yaml.load()` without `Loader=SafeLoader` |

---

## Severity guidance

- **Blocker**: Exploitable in production, exposes credentials/data, bypasses auth
- **Important**: Increases attack surface, violates least privilege, missing validation on a sensitive path
- **Nit**: Theoretical/low-impact, no immediate exploitability
