# CX-View

A local web dashboard for connecting to multiple Checkmarx One tenants and viewing
project and user summaries.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

```bash
python -m app.server
```

Starts on port 8000 by default. If that port is already in use, it automatically
tries 8001, 8002, etc. until it finds a free one (up to 50 attempts) — check the
console output for the port actually used. Override the starting port with the
`CX_VIEW_PORT` environment variable:

```bash
CX_VIEW_PORT=9000 python -m app.server
```

For auto-reload during development (no port auto-increment), use uvicorn directly:

```bash
uvicorn app.main:app --reload --port 8000
```

## Test

```bash
pytest
```

## Notes

- Tenant credentials (refresh token / client secret) are encrypted at rest in a local
  SQLite database using a machine-local key generated on first run.
- The "License Expiration" shown per connection is decoded from the `ast-license` claim
  embedded in the JWT access token, refreshed on each successful Test/Connect.
- The User Summary's "last login" comes from the Keycloak-based IAM users endpoint
  (`{iam_url}/auth/admin/realms/{tenant_id}/users`) and has been verified against a
  real tenant.
- Checkmarx One scopes project/application visibility by IAM group membership,
  separately from role permissions — a client-credentials service account needs to be
  a member of the relevant group(s) (or the tenant's root group) to see projects, even
  if it has roles like `ast-admin`.
