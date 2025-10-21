import json
from datetime import datetime
import sqlite3
from .path_control import PM
from .logger import logger
from .eventFormater import format_events
from .db_strcuture import structure
import json


class ProcessDB():
    _instance = None  # 单例缓存

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ProcessDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return  

        db_path = PM.get_env("EVENTS_DBNEW_PATH")

        logger.info(f"[ProcessDB] 使用数据库路径: {db_path}")
        # check_same_thread=False 保证多线程环境下可用
        self.db_event = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor_event = self.db_event.cursor()
        self.cursor_event.execute(structure.create_table_sql)
        self.db_event.commit()

        self.key_list = structure.defaults
        self._initialized = True  # 标记已初始化

    def _prepare_data(self, data: dict) -> dict:
        """规范化数据（list 转 json）"""
        result = self.key_list.copy()
        result["created_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for key in result.keys():
            if key in data:
                value = data[key]
                if isinstance(value, (list, dict)):
                    result[key] = json.dumps(value, ensure_ascii=False)
                else:
                    result[key] = value
        return result
    
    def _prepare_update_data(self, data: dict) -> dict:
        """专门用于UPDATE的数据预处理"""
        result = {}
        
        for key, value in data.items():
            if key in self.key_list and key != "created_at":  # 防止更新创建时间
                if isinstance(value, (list, dict)):
                    result[key] = json.dumps(value, ensure_ascii=False)
                else:
                    result[key] = value
        
        # 添加更新时间
        if result:
            result["updated_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return result

    # ----------------- CRUD -----------------

    def create_event(self, data: dict) -> int:
        """插入事件，返回 event_id"""
        try:
            row = self._prepare_data(data)
            keys = ",".join(row.keys())
            placeholders = ",".join(["?"] * len(row))
            values = list(row.values())

            sql = f"INSERT INTO events ({keys}) VALUES ({placeholders})"
            self.cursor_event.execute(sql, values)
            self.db_event.commit()
            event_id = self.cursor_event.lastrowid
            logger.info(f"[ProcessDB] 成功插入事件 event_id={event_id}")
            return event_id
        except Exception as e:
            logger.error(f"[ProcessDB] 插入失败: {e}")
            self.db_event.rollback()
            return -1

    def update_event(self, event_id: int, data: dict) -> bool:
        """更新事件"""
        try:
            row = self._prepare_update_data(data)
            set_clause = ", ".join([f"{k}=?" for k in row.keys()])
            values = list(row.values()) + [event_id]

            sql = f"UPDATE events SET {set_clause} WHERE event_id=?"
            self.cursor_event.execute(sql, values)
            self.db_event.commit()
            logger.info(f"[ProcessDB] 更新事件成功 event_id={event_id}")
            return True
        except Exception as e:
            logger.error(f"[ProcessDB] 更新失败: {e}")
            self.db_event.rollback()
            return False

    def delete_event(self, event_id: int) -> bool:
        """删除事件"""
        try:
            sql = "DELETE FROM events WHERE event_id=?"
            self.cursor_event.execute(sql, (event_id,))
            self.db_event.commit()
            logger.info(f"[ProcessDB] 删除事件成功 event_id={event_id}")
            return True
        except Exception as e:
            logger.error(f"[ProcessDB] 删除失败: {e}")
            self.db_event.rollback()
            return False

    # ----------------- 查询函数 -----------------

    def read_event(self, event_id: int) -> dict:
        """根据 event_id 查询单条事件"""
        sql = "SELECT * FROM events WHERE event_id=?"
        self.cursor_event.execute(sql, (event_id,))
        row = self.cursor_event.fetchone()
        if row:
            columns = [desc[0] for desc in self.cursor_event.description]
            res = dict(zip(columns, row))
            return format_events(res)
        return {}
    
    def search_events_undo(self):
        sql = "SELECT * FROM events WHERE done=0"
        self.cursor_event.execute(sql)
        rows = self.cursor_event.fetchall()
        columns = [desc[0] for desc in self.cursor_event.description]
        res = [dict(zip(columns, row)) for row in rows] 
        return format_events(res)


    def search_events_all(self, start_time=None, end_time=None, min_importance=None) -> list:
        """
        查询事件：
        - start_time, end_time: 时间范围 (字符串 'YYYY-MM-DD HH:MM:SS')
        - min_importance: 重要程度下限
        """
        conditions = []
        values = []

        if start_time:
            conditions.append("created_at >= ?")
            values.append(start_time)
        if end_time:
            conditions.append("created_at <= ?")
            values.append(end_time)
        if min_importance is not None:
            conditions.append("importance >= ?")
            values.append(min_importance)

        where_clause = " AND ".join(conditions)
        sql = "SELECT * FROM events"
        if where_clause:
            sql += " WHERE " + where_clause

        self.cursor_event.execute(sql, values)
        rows = self.cursor_event.fetchall()
        columns = [desc[0] for desc in self.cursor_event.description]
        res = [dict(zip(columns, row)) for row in rows] 
        return format_events(res)

