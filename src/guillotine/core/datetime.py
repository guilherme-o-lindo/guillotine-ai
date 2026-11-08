from datetime import UTC, datetime
from zoneinfo import ZoneInfo

LOCAL_TIMEZONE = ZoneInfo("America/Fortaleza")


def to_local_time(value: str) -> str:
    timestamp = datetime.fromisoformat(value)

    timestamp = timestamp.replace(tzinfo=UTC)

    local_timestamp = timestamp.astimezone(LOCAL_TIMEZONE)

    return local_timestamp.strftime("%d/%m/%Y %H:%M:%S")
