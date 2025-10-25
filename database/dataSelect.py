from typing import List, Any, Dict
from scripts.logger import logger


class DataSelect:
    """统一处理多版本 event 数据结构的导出"""

    def __init__(self):
        # 🔹 内部NER字段
        self.in_ner_extract = [
            "dates", "times", "weeks", 
            "places", "persons", "durations", "recurrences","events_extract", "events_full"
        ]

        # 🔹 外部通用字段
        self.in_outter = [
            "event_id", "created_at", "updated_at",
            "tags", "importance", "file_original",
            "file_processed", "done","schema_version"
        ]

        # 🔹 导出字段集合
        self.export_fields = {
            "daily": ["event_id", "dates", "times", "events_full"],
            "detail": self.in_ner_extract + self.in_outter,
        }

        # 🔹 支持的版本
        self.available_versions = {1: "version_1", 2: "version_2"}

    # -----------------------
    # 主入口
    # -----------------------
    def get_infomotions(self, datas: List[Dict], needtype: str) -> List[Dict]:
        """根据 schema_version 自动选择解析函数"""
        if needtype not in self.export_fields:
            raise ValueError(f"不支持的导出类型: {needtype}")

        results = []
        for data in datas:
            version = data.get("schema_version")
            handler = getattr(self, self.available_versions.get(version, ""), None)
            if handler is None:
                logger.error(
                    f"[DataSelect] 不支持的数据版本 id={data.get('event_id')}, "
                    f"支持的版本={list(self.available_versions.keys())}, 当前={version}"
                )
                continue

            try:
                results.append(handler(data, needtype))
            except Exception as e:
                logger.error(f"[DataSelect] 处理事件 {data.get('event_id')} 时出错: {e}")

        return results

    # -----------------------
    # 各版本处理函数
    # -----------------------
    def version_1(self, data: Dict, needtype: str) -> Dict:
        """版本1: 字段直接在顶层"""
        fields = self.export_fields[needtype]
        return {k: data.get(k, None) for k in fields}

    def version_2(self, data: Dict, needtype: str) -> Dict:
        """版本2: NER字段位于 data['ner_extract']"""
        fields = self.export_fields[needtype]
        res = {}
        ner_data = data.get("ner_extract", {})

        for key in fields:
            if key in self.in_ner_extract:
                res[key] = ner_data.get(key)
            elif key in self.in_outter:
                res[key] = data.get(key)
            else:
                logger.warning(f"[DataSelect] 忽略未知字段: {key}")

        return res

    def formator_to_db(self, data: Dict) -> Dict:
        # 适用于schema_version=2
        to_db = {"ner_extract": {}}

        if data == {'done': 1}:
            return data
        
        if int(data['schema_version']) != 2:
            return False
        
        for key in data.keys():
            if key in self.in_ner_extract:
                to_db["ner_extract"][key] = data[key]
            elif key in self.in_outter:
                to_db[key] = data[key]
            else:
                logger.warning(f"[DataSelect] 忽略未知字段: {key}")
        return to_db

# # ✅ 单例
Selector = DataSelect()
# if __name__ == "__main__":
#     print({"done":1}=={"done":1})