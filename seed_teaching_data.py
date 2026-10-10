"""Import only the four fictional course rows into an empty, offline ledger.

No server, dependency or account is required. Never clears or replaces records.
The explicit --db path is the destination; this tool has no implicit ledger path.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import uuid

FIELDS = {"amount_cents", "date", "category", "note"}
EXPECTED = (
    (2300, "2026-09-15", "餐饮", "虚构午饭"),
    (800, "2026-09-16", "交通", "虚构公交"),
    (10000, "2026-09-17", "购物", "虚构购物"),
    (1000, "2026-10-01", "餐饮", "虚构早餐"),
)
TABLE_SQL = """CREATE TABLE IF NOT EXISTS expenses (
    id TEXT PRIMARY KEY,
    amount_cents INTEGER NOT NULL CHECK(amount_cents>0),
    date TEXT NOT NULL, category TEXT NOT NULL, note TEXT NOT NULL,
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
)"""


def load_fixture(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(rows, list) or len(rows) != len(EXPECTED):
        raise ValueError("Fixture must contain exactly the four fictional course rows")
    for row, expected in zip(rows, EXPECTED):
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("Unexpected fixture fields")
        cents = row["amount_cents"]
        if type(cents) is not int or not 0 < cents <= 999999999:
            raise ValueError("Amount must be positive integer cents; bool/float rejected")
        if not isinstance(row["date"], str) or len(row["date"]) != 10:
            raise ValueError("Date must be YYYY-MM-DD")
        if date.fromisoformat(row["date"]).isoformat() != row["date"]:
            raise ValueError("Invalid ISO date")
        if not isinstance(row["category"], str) or row["category"] not in {"餐饮", "交通", "购物", "居家", "其他"}:
            raise ValueError("Invalid course category")
        if not isinstance(row["note"], str) or len(row["note"]) > 60:
            raise ValueError("Invalid course note")
        actual = tuple(row[key] for key in ("amount_cents", "date", "category", "note"))
        if actual != expected:
            raise ValueError("Fixture differs from the four approved fictional rows")
    return rows


def inspect_existing(db: Path) -> None:
    if not db.exists():
        return
    if not db.is_file():
        raise ValueError("Destination exists but is not a database file")
    # Refuse a populated destination without opening it for writes or creating a journal.
    conn = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables - {"expenses"}:
            raise ValueError("Destination contains unrelated tables")
        if "expenses" in tables and conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]:
            raise ValueError("Destination ledger is not empty; nothing was imported")
    finally:
        conn.close()


def import_empty(db: Path, rows: list[dict]) -> dict:
    if db.suffix.lower() not in {".sqlite3", ".db"}:
        raise ValueError("Use an explicit .sqlite3 or .db destination")
    inspect_existing(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(db, timeout=5)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(TABLE_SQL)
        columns = [row[1] for row in conn.execute("PRAGMA table_info(expenses)")]
        if columns != ["id", "amount_cents", "date", "category", "note", "created_at", "updated_at"]:
            raise ValueError("Destination schema differs from this ledger")
        # Recheck under the transaction, so concurrent inserts cannot be overwritten.
        if conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]:
            raise ValueError("Destination ledger became nonempty; nothing was imported")
        for row in rows:
            conn.execute(
                "INSERT INTO expenses (id,amount_cents,date,category,note,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), row["amount_cents"], row["date"], row["category"], row["note"], now, now),
            )
        totals = {
            month: {"records": count, "amount_cents": cents}
            for month, count, cents in conn.execute(
                "SELECT substr(date,1,7),COUNT(*),SUM(amount_cents) FROM expenses GROUP BY substr(date,1,7)"
            )
        }
        expected = {"2026-09": {"records": 3, "amount_cents": 13100}, "2026-10": {"records": 1, "amount_cents": 1000}}
        if totals != expected:
            raise ValueError("Post-insert course totals differ; transaction rolled back")
        conn.commit()
        return {"virtual_data_only": True, "database": str(db), "created_records": 4, "monthly": totals}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Explicit new or empty offline teaching database path")
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("teaching-fixture.json"))
    args = parser.parse_args()
    try:
        result = import_empty(Path(args.db).expanduser().resolve(), load_fixture(args.fixture.resolve()))
    except (ValueError, OSError, sqlite3.Error, json.JSONDecodeError) as exc:
        print(f"Import refused: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
