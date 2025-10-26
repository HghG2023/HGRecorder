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
            r"(?:上午|下午|中午|早上|晚上)?\s?(?:[0-1]?\d|2[0-3])\s?点(?:半|半钟)?(?:\d{1,2}分)?"
            r"|"
            # 中文时 10时10分
            r"\d{1,2}时(?:\d{1,2}分)?"
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

    def chinese_to_digit(self, s: str) -> float:
        if not s:
            return 0
        s = s.strip()
        return CN_NUM.get(s, None) or float(s) if s.isdigit() else 0

    def normalize_absolute(self, match: re.Match) -> str:
        period = match.group(2)
        hour_str = match.group(3)
        minute_str = match.group(4)
        half = match.group(5)

        hour = int(self.chinese_to_digit(hour_str))
        minute = 0

        if half == "半":
            minute = 30
        elif minute_str:
            minute = int(self.chinese_to_digit(minute_str))

        # 时段处理
        if period in PERIOD_MAP:
            if PERIOD_MAP[period] == 12 and hour < 12:
                hour += 12
            elif period == "凌晨" and hour == 12:
                hour = 0

        # 限制小时范围
        hour = max(0, min(hour, 23))
        minute = max(0, min(minute, 59))

        return f"{hour:02d}:{minute:02d}"

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
            m = re.match(r'(\d+|[一二三四五六七八九十]+|几)\s*(分钟|小时|天|日)后', text)
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
