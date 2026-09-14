"""Create the bootstrap admin user from environment variables."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.crud.user import create_superuser
from app.db.session import SessionLocal


def main() -> None:
    """Insert or retrieve the admin account from environment settings."""
    configure_logging()
    settings = get_settings()
    email = settings.effective_admin_email
    password = settings.effective_admin_password
    full_name = settings.effective_admin_full_name

    db = SessionLocal()
    try:
        user = create_superuser(
            db,
            email=email,
            password=password,
            full_name=full_name,
        )
        print(f"Admin ready: id={user.id} email={user.email} role={user.role.value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
