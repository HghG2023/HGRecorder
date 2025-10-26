import re
from typing import List
from datetime import datetime, timedelta
from .BaseExtractor import BaseExtractor

CN_NUM = {
    "一":1, "二":2, "三":3, "四":4, "五":5, "六":6, "七":7, "八":8, "九":9, "十":10,
    "十一":11, "十二":12, "半":0.5, "几":3
}

PERIOD_MAP = {
    "上午": 0, "早上": 0, "中午": 12, "下午": 12, "傍晚": 12, "晚上": 12, "凌晨": 0
}

CN_NUM_PATTERN = r'[一二三四五六七八九十百]+'

class TimeExtractor(BaseExtractor):
    name = "times"

    def __init__(self):
        abs_time_pattern = (
            r"(?P<absolute>"
            r"(?:"
            # 24小时制 HH:MM 或 HH:MM-HH:MM
            r"(?:[01]?\d|2[0-3])[:：][0-5]\d"
            r"(?:\s*[-~到至]\s*(?:[01]?\d|2[0-3])[:：][0-5]\d)?"
            r"|"
            # 中文时间 上午/下午/早上/晚上 10点半 10点10分
            r"(?:上午|下午|中午|早上|晚上|凌晨)?\s*([\d" + CN_NUM_PATTERN + r"]+)\s?点(?:半|半钟)?(?:([\d" + CN_NUM_PATTERN + r"]+)分)?"
            r"|"
            # 中文时 10时10分
            r"([\d" + CN_NUM_PATTERN + r"]+)时(?:([\d" + CN_NUM_PATTERN + r"]+)分)?"
            r")"
            r")"
        )

        # 相对时间（数字/中文数字+单位+后，一会儿、马上、明天、后天、大后天）
        rel_time_pattern = (
            r"(?P<relative>"
            r"((\d+|" + CN_NUM_PATTERN + r"|几)\s*(分钟|小时|天|日))后|"  # 数字+单位+后
            r"一会儿|马上|明天|后天|大后天"
            r")"
        )

        self.pattern = re.compile(f'{abs_time_pattern}|{rel_time_pattern}', re.U)

    def extract(self, text: str) -> List[str]:
        times = []
        for m in self.pattern.finditer(text):
            # 排除楼号/室号等误匹配
            context = text[max(0, m.start()-3):m.end()+3]
            if re.search(r'楼|室|号', context):
                continue

            if m.group("absolute"):
                normalized = self.normalize_absolute(m)
                if normalized:
                    times.append(normalized)
            elif m.group("relative"):
                normalized = self.normalize_relative(m)
                if normalized:
                    times.append(normalized)
        return times

    def chinese_to_digit(self, s: str) -> int:
        if not s:
            return 0
        s = s.strip()
        if s.isdigit():
            return int(s)
        return CN_NUM.get(s, 0)

    def normalize_absolute(self, match: re.Match) -> str:
        time_str = match.group("absolute")

        # 1. 24小时制 HH:MM
        m1 = re.match(r'(\d{1,2})[:：](\d{1,2})', time_str)
        if m1:
            hour = int(m1.group(1))
            minute = int(m1.group(2))
            hour = max(0, min(hour, 23))
            minute = max(0, min(minute, 59))
            return f"{hour:02d}:{minute:02d}"

        # 2. 中文时间（含点、半、分钟、时段）
        m2 = re.match(r'(上午|下午|中午|早上|晚上|凌晨)?\s*([\d' + CN_NUM_PATTERN + r']+)点(?:半|半钟)?(?:([\d' + CN_NUM_PATTERN + r']+)分)?', time_str)
        if m2:
            period = m2.group(1)
            hour_str = m2.group(2)
            minute_str = m2.group(3)
            hour = self.chinese_to_digit(hour_str)
            minute = 0
            if "半" in time_str:
                minute = 30
            elif minute_str:
                minute = self.chinese_to_digit(minute_str)

            # 时段处理
            if period in PERIOD_MAP:
                if PERIOD_MAP[period] == 12 and hour < 12:
                    hour += 12
                elif period == "凌晨" and hour == 12:
                    hour = 0

            hour = max(0, min(hour, 23))
            minute = max(0, min(minute, 59))
            return f"{hour:02d}:{minute:02d}"

        # 3. 中文“时”格式
        m3 = re.match(r'([\d' + CN_NUM_PATTERN + r']+)时(?:([\d' + CN_NUM_PATTERN + r']+)分)?', time_str)
        if m3:
            hour = self.chinese_to_digit(m3.group(1))
            minute = self.chinese_to_digit(m3.group(2)) if m3.group(2) else 0
            hour = max(0, min(hour, 23))
            minute = max(0, min(minute, 59))
            return f"{hour:02d}:{minute:02d}"

        return None

    def normalize_relative(self, match: re.Match) -> str:
        text = match.group("relative")
        now = datetime.now()
        delta = timedelta()
        if not text:
            return None

        if text in ["一会儿", "马上"]:
            delta = timedelta(minutes=10)
        elif text == "明天":
            delta = timedelta(days=1)
        elif text == "后天":
            delta = timedelta(days=2)
        elif text == "大后天":
            delta = timedelta(days=3)
        else:
            m = re.match(r'(\d+|[' + CN_NUM_PATTERN + r']+|几)\s*(分钟|小时|天|日)后', text)
            if m:
                num = self.chinese_to_digit(m.group(1))
                unit = m.group(2)
                if unit in ["分钟"]:
                    delta = timedelta(minutes=num)
                elif unit in ["小时"]:
                    delta = timedelta(hours=num)
                elif unit in ["天", "日"]:
                    delta = timedelta(days=num)
        target_time = now + delta
        return target_time.strftime("%H:%M")

# if __name__ == "__main__":
#     Text = """'英文科技论文写作与学术报告', ' 网络课程 2025秋-英文科技论文写作与学术报告1班 开课时间： 2025-09-22/08:00 至 2025-12-28/23:59'"""
#     print(TimeExtractor().extract(Text))