# db_structure.py
import re

class DBStructure:
    """自动从 CREATE TABLE SQL 推导字段定义 + 版本化支持"""
    def __init__(self, create_sql: str):
        self.create_table_sql = create_sql
        self.CURRENT_VERSION = 2                        # ✅ 当前结构版本
        self.fields = self._parse_fields(create_sql)
        self.defaults = self._infer_defaults()

    def _parse_fields(self, sql):
        content = re.search(r'\((.*)\)', sql, re.DOTALL)
        if not content:
            raise ValueError("[DBStructure] 无法解析SQL结构")
        lines = [l.strip().strip(',') for l in content.group(1).splitlines() if l.strip()]
        fields = {}
        for line in lines:
            parts = line.split()
            name, type_ = parts[0], parts[1].upper()
            fields[name] = type_
        return fields

    def _infer_defaults(self):
        """根据字段类型智能推断默认值"""
        defaults = {}
        for name, type_ in self.fields.items():
            if name == "event_id":
                continue
            elif name == "schema_version":
                defaults[name] = self.CURRENT_VERSION
            elif name == "done":
                defaults[name] = 0
            elif "TEXT" in type_:
                defaults[name] = ""
            elif "INT" in type_:
                defaults[name] = 0
            elif "REAL" in type_:
                defaults[name] = 0.0
            else:
                defaults[name] = None
        return defaults


    def ensure_schema(self, cursor):
        """检查并补齐缺失字段"""
        conn = cursor.connection

        # 🔧 暂存当前 factory 并禁用
        old_factory = conn.row_factory
        conn.row_factory = None  # ✅ 恢复默认 tuple 模式
        raw_cursor = conn.cursor()
        raw_cursor.execute("PRAGMA table_info(events)")
        existing = [c[1] for c in raw_cursor.fetchall()]
        raw_cursor.close()
        conn.row_factory = old_factory  # ✅ 恢复 factory

        for name, type_ in self.fields.items():
            if name not in existing:
                cursor.execute(f"ALTER TABLE events ADD COLUMN {name} {type_}")
                print(f"✅ 自动添加字段: {name}")
        return True

