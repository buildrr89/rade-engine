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
- Scrub report artifacts for obvious sensitive strings before JSON and Markdown write.
- Regression tests in [tests/test_scrubber.py](../tests/test_scrubber.py) prove that both JSON and Markdown outputs are scrubbed at the artifact boundary.
- Preserve only the structural identifiers needed for deterministic review and debugging.

## Hosted persistence controls

- Row Level Security (RLS) policies must use the tenant claim (for example, `tenant_id = current_setting('request.jwt.claims.tenant_id')::UUID`) on every persistence table so no tenant can query another tenant’s `analysis_runs`, `duplicate_clusters`, or `artifacts`.
- Audit logging records the authenticated user/role, tenant_id, run_id, and the action (insert/update/select) whenever a service role bypasses RLS for migrations or background processing.
- Only scrubbed payloads containing normalized `node_ref`, `cluster_fingerprint`, and `rule_id` are persisted to `analysis_runs` JSONB columns; raw sensitive strings are stripped before write, matching the proof slice’s artifact boundary.
- Short retention applies to persisted artifacts: `artifacts` rows auto-expire via an `expires_at` column, and a nightly job deletes runs older than the tenant’s retention policy while keeping the deterministic identifier indexes intact.

## Product rule

Do not ship collector behavior that depends on fake accounts, login bypass, or anti-bot evasion.

## Public repository intake

- Public vulnerability reports must use GitHub Private Vulnerability Reporting.
- Public issues are for reproducible bugs, docs, and collaboration, not sensitive disclosures.
