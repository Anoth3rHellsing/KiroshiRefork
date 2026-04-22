import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

def get_db_path(database_dir: Path) -> Path:
    return database_dir / "kiroshi.db"

def get_connection(database_dir: Path) -> sqlite3.Connection:
    db_path = get_db_path(database_dir)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db(database_dir: Path) -> None:
    conn = get_connection(database_dir)
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS recent_cases (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS memory (
                memory_type TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_learning (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS autosave (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                payload TEXT NOT NULL
            );
        """)
    conn.close()

# Cases
def save_case(database_dir: Path, case_id: str, payload: dict) -> None:
    conn = get_connection(database_dir)
    with conn:
        conn.execute(
            "INSERT INTO cases (case_id, payload, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(case_id) DO UPDATE SET payload=excluded.payload, updated_at=CURRENT_TIMESTAMP",
            (case_id, json.dumps(payload, ensure_ascii=False))
        )
    conn.close()

def load_case(database_dir: Path, case_id: str) -> Optional[dict]:
    conn = get_connection(database_dir)
    row = conn.execute("SELECT payload FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    conn.close()
    if row:
        return json.loads(row["payload"])
    return None

def get_all_cases(database_dir: Path) -> List[dict]:
    conn = get_connection(database_dir)
    rows = conn.execute("SELECT payload FROM cases").fetchall()
    conn.close()
    return [json.loads(row["payload"]) for row in rows]

# Recent Cases
def save_recent_cases(database_dir: Path, payload: list) -> None:
    conn = get_connection(database_dir)
    with conn:
        conn.execute(
            "INSERT INTO recent_cases (id, payload) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
            (json.dumps(payload, ensure_ascii=False),)
        )
    conn.close()

def load_recent_cases(database_dir: Path) -> list:
    conn = get_connection(database_dir)
    row = conn.execute("SELECT payload FROM recent_cases WHERE id = 1").fetchone()
    conn.close()
    if row:
        return json.loads(row["payload"])
    return []

# Settings
def save_settings(database_dir: Path, payload: dict) -> None:
    conn = get_connection(database_dir)
    with conn:
        conn.execute(
            "INSERT INTO settings (id, payload) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
            (json.dumps(payload, ensure_ascii=False),)
        )
    conn.close()

def load_settings(database_dir: Path) -> Optional[dict]:
    conn = get_connection(database_dir)
    row = conn.execute("SELECT payload FROM settings WHERE id = 1").fetchone()
    conn.close()
    if row:
        return json.loads(row["payload"])
    return None

# Memory
def save_memory(database_dir: Path, memory_type: str, payload: dict) -> None:
    conn = get_connection(database_dir)
    with conn:
        conn.execute(
            "INSERT INTO memory (memory_type, payload) VALUES (?, ?) "
            "ON CONFLICT(memory_type) DO UPDATE SET payload=excluded.payload",
            (memory_type, json.dumps(payload, ensure_ascii=False))
        )
    conn.close()

def load_memory(database_dir: Path, memory_type: str) -> Optional[dict]:
    conn = get_connection(database_dir)
    row = conn.execute("SELECT payload FROM memory WHERE memory_type = ?", (memory_type,)).fetchone()
    conn.close()
    if row:
        return json.loads(row["payload"])
    return None

# AI Learning
def save_ai_learning(database_dir: Path, payload: dict) -> None:
    conn = get_connection(database_dir)
    with conn:
        conn.execute(
            "INSERT INTO ai_learning (id, payload) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
            (json.dumps(payload, ensure_ascii=False),)
        )
    conn.close()

def load_ai_learning(database_dir: Path) -> Optional[dict]:
    conn = get_connection(database_dir)
    row = conn.execute("SELECT payload FROM ai_learning WHERE id = 1").fetchone()
    conn.close()
    if row:
        return json.loads(row["payload"])
    return None

# Autosave
def save_autosave(database_dir: Path, payload: dict) -> None:
    conn = get_connection(database_dir)
    with conn:
        conn.execute(
            "INSERT INTO autosave (id, payload) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
            (json.dumps(payload, ensure_ascii=False),)
        )
    conn.close()

def load_autosave(database_dir: Path) -> Optional[dict]:
    conn = get_connection(database_dir)
    row = conn.execute("SELECT payload FROM autosave WHERE id = 1").fetchone()
    conn.close()
    if row:
        return json.loads(row["payload"])
    return None

def migrate_legacy_json_files(database_dir: Path, tracked_cases_dir: Path, app_root_dir: Path) -> None:
    """Migrate legacy .json files to SQLite and rename them to .json.bak."""
    logger = logging.getLogger(__name__)
    init_db(database_dir)

    # 1. Migrate AI Learning
    ai_learning_file = database_dir / "AILearning.json"
    if ai_learning_file.exists():
        try:
            with open(ai_learning_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            save_ai_learning(database_dir, data)
            ai_learning_file.rename(ai_learning_file.with_suffix(".json.bak"))
            logger.info("Migrated AILearning.json")
        except Exception as e:
            logger.error(f"Failed to migrate AILearning.json: {e}")

    # 2. Migrate Recent Cases
    recent_cases_file = database_dir / "recent_cases.json"
    if recent_cases_file.exists():
        try:
            with open(recent_cases_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            save_recent_cases(database_dir, data)
            recent_cases_file.rename(recent_cases_file.with_suffix(".json.bak"))
            logger.info("Migrated recent_cases.json")
        except Exception as e:
            logger.error(f"Failed to migrate recent_cases.json: {e}")

    # 3. Migrate Settings
    settings_file = database_dir / "settings.json"
    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            save_settings(database_dir, data)
            settings_file.rename(settings_file.with_suffix(".json.bak"))
            logger.info("Migrated settings.json")
        except Exception as e:
            logger.error(f"Failed to migrate settings.json: {e}")

    # 4. Migrate Autosave
    autosave_file = app_root_dir / "autosave.json"
    if not autosave_file.exists():
        autosave_file = database_dir / "autosave.json"

    if autosave_file.exists():
        try:
            with open(autosave_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            save_autosave(database_dir, data)
            autosave_file.rename(autosave_file.with_suffix(".json.bak"))
            logger.info(f"Migrated {autosave_file.name}")
        except Exception as e:
            logger.error(f"Failed to migrate autosave.json: {e}")

    # 5. Migrate Memory
    for mem_file in ["kiroshi_memory.json", "manual_memory.json"]:
        mem_path = app_root_dir / mem_file
        if mem_path.exists():
            try:
                with open(mem_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                save_memory(database_dir, mem_file, data)
                mem_path.rename(mem_path.with_suffix(".json.bak"))
                logger.info(f"Migrated {mem_file}")
            except Exception as e:
                logger.error(f"Failed to migrate {mem_file}: {e}")

    # 6. Migrate Individual Cases
    for file_path in database_dir.glob("*.json"):
        if file_path.name.lower() in {"recent_cases.json", "settings.json", "ailearning.json", "autosave.json", "case_tabs_memory.json"}:
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            case_id = data.get("case_id", file_path.stem)
            save_case(database_dir, case_id, data)
            file_path.rename(file_path.with_suffix(".json.bak"))
            logger.info(f"Migrated case {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to migrate case {file_path.name}: {e}")

    if tracked_cases_dir.exists():
        for file_path in tracked_cases_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                case_id = data.get("case_id", file_path.stem.replace("_Active", ""))
                save_case(database_dir, case_id, data)
                file_path.rename(file_path.with_suffix(".json.bak"))
                logger.info(f"Migrated tracked case {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to migrate tracked case {file_path.name}: {e}")
