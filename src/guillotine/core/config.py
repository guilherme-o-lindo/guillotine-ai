import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]

load_dotenv(ROOT_DIR / ".env")


class Settings:
    BASE_URL: str = os.getenv(
        "GUILLOTINE_BASE_URL",
        "http://localhost:20128/v1",
    )
    API_KEY: str = os.getenv("GUILLOTINE_API_KEY", "")
    MODEL: str = os.getenv("GUILLOTINE_MODEL", "")


settings = Settings()
