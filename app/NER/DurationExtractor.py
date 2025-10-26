import re
from typing import List
from .BaseExtractor import BaseExtractor

class DurationExtractor(BaseExtractor):
    name = "durations"

    def __init__(self):
        # ✅ 支持以下情况：
        # 1️⃣ 数字形式：3天、10分钟、1个半小时、2.5小时
        # 2️⃣ 汉字数字：三天、两小时半、一个小时左右
        # 3️⃣ 模糊/口语：一阵子、一会儿、一段时间、好久、半个小时、好几天
        # 4️⃣ 近似/修饰：大约三天、差不多两小时、将近5分钟、不到十秒、约一个半小时
        # 5️⃣ 范围/复合：三到五天、两三分钟、十几秒
        # 6️⃣ 多单位复合：1小时20分钟、两天三夜、三年两个月、1天半
        number = r'(?:\d+(?:\.\d+)?|[一二三四五六七八九十百千万两半几十多]+)'
        unit = r'(?:年|个月|月|星期|周|天|日|小时|钟头|分钟|分|秒|瞬间|阵子|会儿|段时间|下)'
        approx = r'(?:大约|大概|大致|大体|大多|差不多|将近|约|不到|接近|快要|整整|至少|顶多|不超过|不满)?'
        suffix = r'(?:左右|上下|多|不到)?'
        connector = r'(?:半|[零一二三四五六七八九十几]+[个又]半)?'

        # 匹配复合时间，如 “1小时20分钟”、“两天三夜”、“三年两个月”、“1天半”
        compound = (
            fr'(?:{approx}\s*{number}\s*{unit}(?:\s*{connector}\s*{unit})?(?:\s*(?:到|至|~|-)\s*{number}\s*{unit})?\s*{suffix})'
        )

        # 匹配模糊时间词
        fuzzy = (
            r'(?:一阵子|一会儿|一小会儿|一大段时间|好久|好长时间|很久|片刻|瞬间|刹那|转眼间|一下子|一段时间|短暂时间|长时间|好几天|好些天|几天几夜)'
        )

        self.pattern = re.compile(
            fr'(?P<duration>{compound}|{fuzzy})',
            re.U
        )

    def extract(self, text: str) -> List[str]:
        return [m.group("duration").strip() for m in self.pattern.finditer(text)]
