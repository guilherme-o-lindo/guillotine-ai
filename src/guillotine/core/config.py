import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[3]

load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    BASE_URL: str
    API_KEY: str
    MODEL: str
    TIMEOUT_SECONDS: float = 60.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            BASE_URL=os.getenv(
                "GUILLOTINE_BASE_URL",
                "http://localhost:20128/v1",
            ),
            API_KEY=os.getenv("GUILLOTINE_API_KEY", ""),
            MODEL=os.getenv("GUILLOTINE_MODEL", ""),
            TIMEOUT_SECONDS=float(os.getenv("GUILLOTINE_TIMEOUT", "60")),
        )

    def validate(self) -> None:
        if not self.BASE_URL.strip():
            raise ValueError("GUILLOTINE_BASE_URL não configurada.")

        if not self.MODEL.strip():
            raise ValueError("GUILLOTINE_MODEL não configurado.")

        if self.TIMEOUT_SECONDS <= 0:
            raise ValueError("GUILLOTINE_TIMEOUT deve ser maior que zero.")


settings = Settings.from_env()
settings.validate()
