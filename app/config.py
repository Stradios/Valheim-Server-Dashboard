import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # ------------------------------------------------------------------
    # Database (SQLite by default, persisted under /app/data)
    # ------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:////app/data/valpanel.db",  # goes into the mapped /mnt/apps/valpanel/data
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------
    # Docker / Valheim settings
    # ------------------------------------------------------------------
    # Default Valheim image
    VALHEIM_IMAGE = os.environ.get("VALHEIM_IMAGE", "lloesche/valheim-server")

    # Port pool for servers (3 ports per server: base, base+1, base+2)
    VALHEIM_PORT_RANGE_START = int(os.getenv("VALHEIM_PORT_RANGE_START", "24560"))
    VALHEIM_PORT_RANGE_END = int(os.getenv("VALHEIM_PORT_RANGE_END", "24660"))
    VALHEIM_PORT_BLOCK_SIZE = int(os.getenv("VALHEIM_PORT_BLOCK_SIZE", "3"))

    # Where to store data for each Valheim container inside the panel container.
    # Host path is provided via Docker volumes.
    DATA_ROOT = os.getenv("DATA_ROOT", "/servers")

    # ------------------------------------------------------------------
    # Flask / session
    # ------------------------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")  # change via env in prod

    # Later: you can add MAIL_* settings for invite emails, etc.

