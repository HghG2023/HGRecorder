import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from .BaseExtractor import BaseExtractor

class DateExtractor(BaseExtractor):
    name = "dates"

    def __init__(self):
        # 支持多类型中文、数字、相对日期
        self.pattern = re.compile(
            r'(?P<date>('
            # 绝对日期
            r'\d{2,4}\s*[年/-]\s*\d{1,2}\s*[月/-]\s*\d{1,2}\s*[日号]?|'     # 2025年10月26日
            r'\d{1,2}\s*[月/-]\s*\d{1,2}\s*[日号]?|'                        # 10月26号
            # 汉字日期
            r'[一二三四五六七八九十]{1,3}\s*月\s*[一二三四五六七八九十]{1,3}\s*[日号]?|'  # 十月二十六日
            # 相对日期
            r'(今天|明天|昨天|前天|后天|大前天|大后天)|'
            # 周次表达
            r'(本周|下周|上周)?(周|星期)[一二三四五六天日]|'
            # 月份相对表达
            r'(上|本|下)个?月(\d{1,2}|[一二三四五六七八九十]{1,3})?[日号]?|'
            # 特殊节日与模糊时间
            r'(年底|年初|月底|月初|国庆节|春节|中秋节|元旦|圣诞节)'
            r'))',
            re.U
        )

    def extract(self, text: str, default: str = "tomorrow"):
        """
        从文本中提取并标准化所有日期。
        若未匹配到日期，可通过 default 参数指定默认返回：
        - "today"    → 返回今天
        - "tomorrow" → 返回明天
        - None       → 返回空列表
        """
        dates = [m.group("date").strip() for m in self.pattern.finditer(text)]
        res = self.normalize(dates)

        if not res:
            if default == "today":
                res.append(datetime.now().strftime("%Y-%m-%d"))
            elif default == "tomorrow":
                res.append((datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))
            # 若 default=None，则保持空结果

        res = self.filter_valid_dates(res)

        return res
    
    def filter_valid_dates(self, dates):
        """
        过滤掉不合法的日期字符串，只保留能解析成 YYYY-MM-DD 的日期
        """
        valid = []
        for d in dates:
            try:
                # 尝试解析，如果成功则保留
                datetime.strptime(d, "%Y-%m-%d")
                valid.append(d)
            except:
                continue
        return valid

    def normalize(self, dates):
        """将提取的日期标准化为 YYYY-MM-DD"""
        base = datetime.now().date()
        today = base
        normalized = []

        chinese_num_map = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10
        }

        def chinese_to_int(chs: str):
            """简单汉字数字转阿拉伯"""
            if not chs:
                return None
            total = 0
            if len(chs) == 1:
                return chinese_num_map.get(chs, None)
            if len(chs) == 2 and chs[0] == "十":
                return 10 + chinese_num_map.get(chs[1], 0)
            if len(chs) == 2 and chs[1] == "十":
                return chinese_num_map.get(chs[0], 0) * 10
            if len(chs) == 3 and chs[1] == "十":
                return chinese_num_map.get(chs[0], 0) * 10 + chinese_num_map.get(chs[2], 0)
            return None

        for d in dates:
            d = d.strip()

            # ✅ 相对日期
            rel_days = {
                "今天": 0, "明天": 1, "后天": 2, "大后天": 3,
                "昨天": -1, "前天": -2, "大前天": -3
            }
            if d in rel_days:
                normalized.append((base + timedelta(days=rel_days[d])).isoformat())
                continue

            # ✅ 周次表达
            match_week = re.match(r'(上|本|下)?(周|星期)([一二三四五六天日])', d)
            if match_week:
                prefix, _, day_ch = match_week.groups()
                week_offset = {"上": -1, "本": 0, "下": 1}.get(prefix or "本", 0)
                weekday_target = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "天": 6, "日": 6}[day_ch]
                # 本周一为基准
                monday = base - timedelta(days=base.weekday())
                target_date = monday + timedelta(days=weekday_target + 7 * week_offset)
                normalized.append(target_date.isoformat())
                continue

            # ✅ 月份相对表达，如“下个月15号”、“本月十号”
            match_month = re.match(r'(上|本|下)个?月(?P<day>\d{1,2}|[一二三四五六七八九十]{1,3})?', d)
            if match_month:
                month_offset = {"上": -1, "本": 0, "下": 1}[match_month.group(1)]
                new_date = base + relativedelta(months=month_offset)
                day_str = match_month.group("day")
                if day_str:
                    if day_str.isdigit():
                        day = int(day_str)
                    else:
                        day = chinese_to_int(day_str)
                    new_date = new_date.replace(day=min(day, 28))  # 避免月溢出
                normalized.append(new_date.isoformat())
                continue

            # ✅ 汉字日期（如“十月二十六日”）
            match_cn = re.match(r'([一二三四五六七八九十]{1,3})月([一二三四五六七八九十]{1,3})', d)
            if match_cn:
                month = chinese_to_int(match_cn.group(1))
                day = chinese_to_int(match_cn.group(2))
                try:
                    normalized.append(datetime(base.year, month, day).date().isoformat())
                except Exception:
                    normalized.append(d)
                continue

            # ✅ 阿拉伯日期，如 2025年10月26日 / 10月26日
            match_num = re.match(r'(?:(\d{2,4})\s*[年/-])?\s*(\d{1,2})\s*[月/-]\s*(\d{1,2})', d)
            if match_num:
                year = match_num.group(1)
                month = int(match_num.group(2))
                day = int(match_num.group(3))
                year = int(year) if year else base.year
                try:
                    normalized.append(datetime(year, month, day).date().isoformat())
                except Exception:
                    normalized.append(d)
                continue

            # ✅ 模糊时间（如“年底”、“国庆节”）
            fuzzy_map = {
                "年底": datetime(base.year, 12, 31),
                "年初": datetime(base.year, 1, 1),
                "月初": datetime(base.year, base.month, 1),
                "月底": datetime(base.year, base.month, 28),
                "国庆节": datetime(base.year, 10, 1),
                "中秋节": datetime(base.year, 9, 17),  # 估值，因农历需另算
                "春节": datetime(base.year, 2, 10),    # 示例
                "元旦": datetime(base.year, 1, 1),
                "圣诞节": datetime(base.year, 12, 25),
            }
            if d in fuzzy_map:
                normalized.append(fuzzy_map[d].date().isoformat())
                continue

            normalized.append(d)  # fallback

        return normalized


