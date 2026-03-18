# SECURITY_BASELINE

## Controls

- Authentication is required for hosted mode.
- Tenant isolation is required for hosted mode.
- Encryption in transit is required.
- Encryption at rest is required.
- Payload validation happens before persistence.
- Audit logging is required.
- Short raw data retention is the default.
- Secure artifact access is required.
- Secrets live in a secrets manager in production.

## Data handling

- Persist normalized structural data by default.
- Persist raw captures only when strictly needed.
- Encrypt retained raw captures.
- Support deletion-by-default for sensitive customers.

## Product rule

Do not ship collector behavior that depends on fake accounts, login bypass, or anti-bot evasion.
