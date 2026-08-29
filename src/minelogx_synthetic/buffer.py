from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


@dataclass(frozen=True)
class BufferedEvent:
    message_id: str
    topic: str
    payload: dict[str, Any]


class PersistentBuffer:
    def __init__(self, path: str | Path, max_events: int = 100_000) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_events = max_events
        self.connection = sqlite3.connect(self.path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS buffered_events (
                message_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                payload TEXT NOT NULL,
                event_timestamp TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                asset_id TEXT NOT NULL,
                sequence_no INTEGER NOT NULL,
                inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> PersistentBuffer:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def __len__(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM buffered_events").fetchone()
        return int(row[0])

    def enqueue(self, topic: str, event: dict[str, Any]) -> bool:
        if len(self) >= self.max_events:
            raise BufferError(f"Persistent buffer limit reached ({self.max_events} events)")
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO buffered_events
                (message_id, topic, payload, event_timestamp, tenant_id, asset_id, sequence_no)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["message_id"],
                topic,
                json.dumps(event, separators=(",", ":")),
                event["timestamp"],
                event["tenant_id"],
                event["asset_id"],
                event["sequence_no"],
            ),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def pending(self, limit: int = 100) -> Iterator[BufferedEvent]:
        rows = self.connection.execute(
            """
            SELECT message_id, topic, payload
            FROM buffered_events
            ORDER BY tenant_id, asset_id, event_timestamp, sequence_no, inserted_at
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        for message_id, topic, payload in rows:
            yield BufferedEvent(message_id, topic, json.loads(payload))

    def acknowledge(self, message_id: str) -> None:
        self.connection.execute(
            "DELETE FROM buffered_events WHERE message_id = ?", (message_id,)
        )
        self.connection.commit()
