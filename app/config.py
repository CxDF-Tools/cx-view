from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "cx-view"
APP_AUTHOR = "cx-view"

DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "cx_view.db"
FERNET_KEY_PATH = DATA_DIR / "secret.key"
SESSION_KEY_PATH = DATA_DIR / "session.key"

EXCLUDED_USER_EMAILS = {
    "ai-assist@noreply.checkmarx.com",
    "david.flynn@checkmarx.com",
}
