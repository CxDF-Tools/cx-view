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
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000

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
  (`{iam_url}/auth/admin/realms/{tenant_id}/users`); the exact response field name for
  last login was not directly inspected pre-build — verify against a real tenant if it
  shows "unavailable" for all users.
