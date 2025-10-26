import re
from typing import List
from .BaseExtractor import BaseExtractor

class PlaceExtractor(BaseExtractor):
    name = "places"

    def __init__(self):
        # 匹配多种场所类型，包括口语、书面、混合中文英文形式
        place_keywords = [
            "店", "馆", "楼", "区", "街", "路", "餐厅", "饭店", 
            "咖啡厅", "超市", "校区", "办公室", "宿舍", "商场",
            "地铁站", "公交站", "图书馆", "影院", "实验室",
            "园", "广场", "中心", "市场", "工厂", "医院"
        ]
        # 允许中文、英文、数字、·、-、()，前面可以有修饰词
        place_pattern = rf'(?P<place>[\u4e00-\u9fa5A-Za-z0-9·\-\（\）()]+(?:{"|".join(place_keywords)}))'
        self.pattern = re.compile(place_pattern, re.U)

        # 口语化修饰词，如“附近”“旁边”“对面”
        self.modifiers = ["附近", "旁边", "对面", "旁侧", "旁", "旁边的"]

    def extract(self, text: str) -> List[str]:
        matches = [m.group("place") for m in self.pattern.finditer(text)]
        # 如果存在口语化修饰词，附加提取
        for mod in self.modifiers:
            for m in re.finditer(rf'([\u4e00-\u9fa5A-Za-z0-9·\-\（\）()]+){mod}', text):
                if m.group(1) not in matches:
                    matches.append(m.group(1))
        return matches
