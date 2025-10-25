# adapter.py
import json
from datetime import datetime

class DataAdapter:
    """实现字典数据与数据库格式互转"""

    @staticmethod
    def to_db(data: dict, defaults: dict) -> dict:
        """
        将 Python 字典数据转换为数据库格式数据
        
        Args:
            data (dict): Python 字典数据
            defaults (dict): 数据库字段默认值
        
        Returns:
            dict: 数据库格式数据
        """
        row = defaults.copy()
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                # 将列表或字典数据转换为 JSON 字符串
                row[k] = json.dumps(v, ensure_ascii=False)
            else:
                row[k] = v
        row["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not row.get("created_at"):
            # 如果 created_at 字段不存在，则设置当前时间
            row["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return row

    @staticmethod
    def from_db(row: dict) -> dict:
        """DB -> Python dict"""
        if not row:
            return {}
        d = {}
        for k, v in row.items():
            if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                try:
                    d[k] = json.loads(v)
                except Exception:
                    d[k] = v
            else:
                d[k] = v
        return d
