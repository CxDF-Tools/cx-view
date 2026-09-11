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
./run.sh
```

or directly:

```bash
python -m app.server
```

Starts on the port set by `CX_VIEW_PORT` in the `.env` file at the repo root
(defaults to `8000` if unset). If that port is already in use, it automatically
tries the next one up (8001, 8002, ...) until it finds a free one (up to 50
attempts) — check the console output for the port actually used.

To change the starting port, edit `CX_VIEW_PORT` in `.env`, or override it for a
single run:

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

## Local Data Storage

CX-View stores its SQLite database and encryption keys in an OS-specific local
app-data directory (via `platformdirs`), **not** inside the repo — this location is
never tracked by git.

| OS      | Location |
|---------|----------|
| macOS   | `~/Library/Application Support/cx-view/` |
| Linux   | `$XDG_DATA_HOME/cx-view/` (typically `~/.local/share/cx-view/`) |
| Windows | `%LOCALAPPDATA%\cx-view\cx-view\` (typically `C:\Users\<you>\AppData\Local\cx-view\cx-view\`) |

That directory contains:

- `cx_view.db` — the SQLite database (saved tenant connections; credential fields are
  encrypted)
- `secret.key` — the Fernet key used to encrypt/decrypt credentials (created on first
  use)
- `session.key` — the key used to sign the browser session cookie

To confirm the exact path on your machine, run (from the project root, with the venv
active):

```bash
python -c "from app.config import DB_PATH; print(DB_PATH)"
```

### Resetting / testing a fresh install

Deleting the database is safe — the app recreates it automatically (with empty
tables) the next time it starts, so there's nothing else to set up.

**macOS**

```bash
rm "$HOME/Library/Application Support/cx-view/cx_view.db"
```

**Linux**

```bash
rm "${XDG_DATA_HOME:-$HOME/.local/share}/cx-view/cx_view.db"
```

**Windows (PowerShell)**

```powershell
Remove-Item "$env:LOCALAPPDATA\cx-view\cx-view\cx_view.db"
```

To simulate a completely fresh install (no saved connections *and* new encryption
keys, meaning any old encrypted values would no longer be decryptable), delete the
whole directory instead of just the `.db` file — e.g. on macOS:
`rm -rf "$HOME/Library/Application Support/cx-view"` (swap in the Linux/Windows paths
above as needed).

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
