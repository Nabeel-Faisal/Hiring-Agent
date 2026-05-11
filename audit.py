import asyncio
import json
from datetime import datetime
from pathlib import Path
from config import AUDIT_LOG_PATH

_lock = asyncio.Lock()


async def log_event(event_type: str, data: dict) -> None:
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "event": event_type,
        **data
    }
    line = json.dumps(entry, default=str) + "\n"
    async with _lock:
        Path(AUDIT_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
