import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

from models.trade import Trade

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB_PATH = os.path.join(ROOT_DIR, "backend", "alphamind.db")
DB_PATH = os.getenv("ALPHAMIND_DB_PATH", DEFAULT_DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                payload TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                market_regime TEXT NOT NULL,
                decision TEXT,
                confidence REAL,
                payload TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                position_size REAL NOT NULL,
                desired_entry REAL NOT NULL,
                fill_price REAL NOT NULL,
                commission_fee REAL NOT NULL,
                stop_loss REAL NOT NULL,
                target REAL NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                exit_price REAL,
                exit_reason TEXT,
                exit_timestamp TEXT,
                raw_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def insert_event(name: str, payload: Dict[str, Any], timestamp: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO events (name, payload, timestamp) VALUES (?, ?, ?)",
            (name, json.dumps(payload), timestamp),
        )
        conn.commit()


def insert_decision(
    symbol: str,
    market_regime: str,
    decision: Optional[str],
    confidence: Optional[float],
    payload: Dict[str, Any],
    timestamp: str,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO decisions (symbol, market_regime, decision, confidence, payload, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (symbol, market_regime, decision, confidence, json.dumps(payload), timestamp),
        )
        conn.commit()


def insert_trade(trade: Trade) -> None:
    data = trade.model_dump(mode="json")
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO trades (
                id, symbol, action, position_size, desired_entry, fill_price, commission_fee,
                stop_loss, target, status, timestamp, exit_price, exit_reason, exit_timestamp, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["symbol"],
                data["action"],
                data["position_size"],
                data["desired_entry"],
                data["fill_price"],
                data["commission_fee"],
                data["stop_loss"],
                data["target"],
                data["status"],
                data["timestamp"],
                data.get("exit_price"),
                data.get("exit_reason"),
                data.get("exit_timestamp"),
                json.dumps(data),
            ),
        )
        conn.commit()


def fetch_recent_events(limit: int = 100) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT name, payload, timestamp FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"name": row["name"], "payload": json.loads(row["payload"]), "timestamp": row["timestamp"]}
        for row in rows
    ]


def fetch_recent_decisions(limit: int = 50) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT symbol, market_regime, decision, confidence, payload, timestamp "
            "FROM decisions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "symbol": row["symbol"],
            "market_regime": row["market_regime"],
            "decision": row["decision"],
            "confidence": row["confidence"],
            "payload": json.loads(row["payload"]),
            "timestamp": row["timestamp"],
        }
        for row in rows
    ]


def fetch_recent_trades(limit: int = 50) -> List[Trade]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT raw_json FROM trades ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
    trades = []
    for row in rows:
        data = json.loads(row["raw_json"])
        trades.append(Trade(**data))
    return trades


init_db()
