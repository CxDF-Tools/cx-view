import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "cx-view"
APP_AUTHOR = "cx-view"

# Starting port for the local server; if it's already in use, app/server.py
# increments from here until a free port is found. Override with CX_VIEW_PORT.
DEFAULT_PORT = int(os.environ.get("CX_VIEW_PORT", "8000"))
MAX_PORT_ATTEMPTS = 50

DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "cx_view.db"
FERNET_KEY_PATH = DATA_DIR / "secret.key"
SESSION_KEY_PATH = DATA_DIR / "session.key"

EXCLUDED_USER_EMAILS = {
    "ai-assist@noreply.checkmarx.com",
    "david.flynn@checkmarx.com",
}
