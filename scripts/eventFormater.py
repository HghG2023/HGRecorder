import json
from datetime import datetime
from typing import Union, List, Dict, Any

def format_events(data: Union[Dict[str, Any], List[Dict[str, Any]]],
                  flatten_persons: bool = True) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    格式化数据库查询结果（支持单条或多条事件数据）

    参数：
        data: dict 或 list[dict]
        flatten_persons: 是否将 persons 转为一维人名列表（默认 True）

    返回：
        格式化后的 dict 或 list[dict]
    """

    def _format_one(event: Dict[str, Any]) -> Dict[str, Any]:
        formatted = {}
        for key, value in event.items():

            # ---------- 1️⃣ 空值处理 ----------
            if value in ("", "None", None):
                formatted[key] = None
                continue

            # ---------- 2️⃣ 尝试解析 JSON ----------
            if isinstance(value, str):
                stripped = value.strip()
                if (stripped.startswith("[") and stripped.endswith("]")) or (
                    stripped.startswith("{") and stripped.endswith("}")
                ):
                    try:
                        parsed = json.loads(stripped)

                        # persons 字段特别处理
                        if key == "persons" and isinstance(parsed, list):
                            cleaned = []
                            for item in parsed:
                                if isinstance(item, list):
                                    non_empty = [x.strip() for x in item if isinstance(x, str) and x.strip()]
                                    if non_empty:
                                        cleaned.append(non_empty[0] if flatten_persons else non_empty)
                                elif isinstance(item, str) and item.strip():
                                    cleaned.append(item.strip())

                            formatted[key] = cleaned
                        else:
                            formatted[key] = parsed
                        continue
                    except json.JSONDecodeError:
                        pass  # 如果不是合法 JSON，就继续下面的逻辑

            # ---------- 3️⃣ 格式化日期 / 时间 ----------
            if key in ("created_at", "dates", "times"):
                if isinstance(value, str):
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
                        try:
                            formatted[key] = datetime.strptime(value, fmt).isoformat()
                            break
                        except ValueError:
                            continue
                    else:
                        formatted[key] = value
                    continue

            # ---------- 4️⃣ 路径统一符号 ----------
            if key.startswith("file_") and isinstance(value, str):
                formatted[key] = value.replace("\\", "/")
                continue

            # ---------- 5️⃣ 其他字段保持原样 ----------
            formatted[key] = value

        return formatted

    # ---------- 6️⃣ 支持单条与多条 ----------
    if isinstance(data, dict):
        return _format_one(data)
    elif isinstance(data, list):
        return [_format_one(item) for item in data]
    else:
        raise TypeError("format_events: data 必须是 dict 或 list[dict]")
