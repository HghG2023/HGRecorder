import re
from typing import List
from .BaseExtractor import BaseExtractor

class PersonExtractor(BaseExtractor):
    """提取文本中出现的人名、称谓、@引用（中英文混合+空格容忍+连续匹配）"""
    name = "persons"

    def __init__(self):
        self.pattern = re.compile(
            r'(?P<person>'
            # 允许中英文混合 + 称谓 + @引用 + 容忍空格
            r'@\s*[\u4e00-\u9fa5A-Za-z0-9_ ]+'
            r'|'
            r'([A-Za-z\u4e00-\u9fa5]{1,10}\s*(老师|总|经理|主任|哥|姐|导师|leader|mentor|manager|teacher|boss))'
            r'|'
            r'([老小大]?\s*[A-Za-z\u4e00-\u9fa5]{1,3}\s*(哥|姐|老师|总|主任|经理)?)'
            r'|'
            r'(老师|同学|同事|同学们|同事们|组长|队长|部长|主任|经理|领导|负责人|导师|校长|朋友|兄弟|姐妹|伙伴|客户|嘉宾|大家|各位|team|leader|mentor|manager|boss|teacher|mentor|manager|client|guys|friends|all|teammates)'
            r'|'
            r'([A-Z][a-z]{1,15}(\s+[A-Z][a-z]{1,15})?)'
            r'|'
            r'([\u4e00-\u9fa5]{2,3})'
            r')',
            re.U
        )

    def extract(self, text: str) -> List[str]:
        """提取人名、称谓、引用等，并合并连续匹配"""
        results = []
        for m in self.pattern.finditer(text):
            person = re.sub(r'\s+', ' ', m.group("person").strip())
            # 去掉表情、标点
            person = re.sub(r'[\[\]【】()（）]', '', person)
            if len(person) < 2:
                continue
            # 去掉无意义单词
            if person.lower() in {"the", "and", "you", "me", "we", "to", "a", "in"}:
                continue
            results.append(person)

        # 合并相邻匹配成一个连续段（可选）
        merged = []
        for r in results:
            if not merged or not merged[-1] in text[text.find(merged[-1]):text.find(r)]:
                merged.append(r)
        # 去重
        return list(dict.fromkeys(merged))
