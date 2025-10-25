# DBprocessor.py
from .structure import DBStructure
from .adapter import DataAdapter
import sqlite3, json
from datetime import datetime
from scripts.logger import logger
from scripts.path_control import PM

class ProcessDB:
    _instance = None

    def __new__(cls, *a, **kw):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        db_path = PM.get_env("EVENTS_DBNEW_PATH")
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = self._dict_factory
        self.cursor = self.db.cursor()

        # 初始化结构
        self.structure = DBStructure("""
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                importance REAL,
                tags TEXT,
                file_original TEXT,
                file_processed TEXT,
                updated_at TEXT,
                done INTEGER,
                ner_extract TEXT,
                schema_version INTEGER
            )
        """)
        self.cursor.execute(self.structure.create_table_sql)
        self.structure.ensure_schema(self.cursor)
        self.db.commit()

        self._initialized = True

    @staticmethod
    def _dict_factory(cursor, row):
        d = {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        return d

    # ---------------- CRUD ----------------

    def exciting(self, event_id: int) -> bool:
        """
        判断指定 event_id 的事件是否存在于数据库中。

        返回：
            True  — 存在
            False — 不存在或查询失败
        """
        try:
            self.cursor.execute("SELECT 1 FROM events WHERE event_id = ? LIMIT 1", (event_id,))
            result = self.cursor.fetchone()
            return result is not None

        except sqlite3.Error as e:
            logger.error(f"[exciting] 查询事件是否存在失败: {e}")
            return False
        
    def create_event(self, data: dict) -> int:
        try:
            row = DataAdapter.to_db(data, self.structure.defaults)
            keys = ",".join(row.keys())
            placeholders = ",".join("?" * len(row))
            sql = f"INSERT INTO events ({keys}) VALUES ({placeholders})"
            self.cursor.execute(sql, list(row.values()))
            self.db.commit()
            logger.info(f"Event created with ID: {self.cursor.lastrowid}")
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return -1

    def update_event(self, event_id: int, data: dict) -> bool:
        if not self.exciting(event_id):
            return False
        try:
            row = DataAdapter.to_db(data, {})
            set_clause = ", ".join([f"{k}=?" for k in row.keys()])
            sql = f"UPDATE events SET {set_clause} WHERE event_id=?"
            self.cursor.execute(sql, list(row.values()) + [event_id])
            self.db.commit()
            logger.info(f"Event updated with ID: {event_id}, data: {data}")
            return True
        except Exception as e:
            logger.error(f"Error updating event with ID {event_id}: {e}")
            return False

    
    def delete_event(self, event_id: int) -> bool:
        if not self.exciting(event_id):
            return False
        self.cursor.execute("DELETE FROM events WHERE event_id=?", (event_id,))
        self.db.commit()
        logger.info(f"Event deleted with ID: {event_id}")
        return True

    def read_event(self, event_id: int) -> dict:
        if not self.exciting(event_id):
            return False
        self.cursor.execute("SELECT * FROM events WHERE event_id=?", (event_id,))
        row = self.cursor.fetchone()
        return DataAdapter.from_db(row)

    def search_events_all(self) -> list:
        self.cursor.execute("SELECT * FROM events")
        rows = self.cursor.fetchall()
        return [DataAdapter.from_db(r) for r in rows]
    
    def search_events_undo(self) -> list:
        self.cursor.execute("SELECT * FROM events WHERE done=0")
        rows = self.cursor.fetchall()
        return [DataAdapter.from_db(r) for r in rows]

