import re

class DB_Structure:
    """自动从 CREATE TABLE SQL 推导出字段默认值结构"""

    def __init__(self):
        # === 原始 SQL 定义 ===
        self.create_table_sql = """
                    CREATE TABLE IF NOT EXISTS events (
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        created_at TEXT NOT NULL,
                        dates TEXT,
                        times TEXT,
                        weeks TEXT,
                        persons TEXT,
                        places TEXT,
                        events_extract TEXT,
                        events_full TEXT,
                        durations TEXT,
                        event_type TEXT,
                        importance INTEGER,
                        confidence REAL,
                        tags TEXT,
                        file_original TEXT,
                        file_processed TEXT,
                        updated_at TEXT,
                        done INTEGER  
                    )"""

        # === 自动推导出的默认值结构 ===
        self.defaults = self._parse_and_infer(self.create_table_sql)

    def _parse_and_infer(self, sql: str) -> dict:
        """从 SQL 提取字段并推断默认值"""
        content = re.search(r'\((.*)\)', sql, re.DOTALL)
        if not content:
            raise ValueError("无法从 SQL 中提取字段定义。")

        column_defs = [c.strip().rstrip(',') for c in content.group(1).splitlines() if c.strip()]
        defaults = {}

        for col_def in column_defs:
            m = re.match(r'(\w+)\s+(\w+)', col_def)
            if not m:
                continue
            name, col_type = m.groups()
            col_type = col_type.upper()

            if name=="done":
                defaults[name] = 0
            else:
                defaults[name] = None
        
        defaults.pop("event_id", None)
        return defaults


structure = DB_Structure()