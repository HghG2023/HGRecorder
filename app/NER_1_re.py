import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from scripts.Tools import r, w
from scripts.path_control import PM
from scripts.unique_string_generate import unique_name  # pip install python-dateutil


class NERProcessor:
    def __init__(self):
        """
        命名实体识别（NER）初始化：
        支持日期、时间、地点、人物、事件、持续时间、周期重复模式（如每周一、每隔三天等）
        """

        # ---------- 年月日（多格式） ----------
        self.date_full = re.compile(
            r"(?P<date_full>("
            r"\d{4}[年/-]\s?\d{1,2}[月/-]\s?\d{1,2}[日号]?"                         # 2025-9-30 / 2025年9月30日
            r"|\d{4}\s?年\s?\d{1,2}\s?月\s?\d{1,2}\s?[日号]?"                       # 2025 年 9 月 30 日
            r"|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?"                                 # 09/30 or 09/30/2025
            r"))"
        )

        # 月日（无年份）
        self.date_md = re.compile(
            r"(?P<date_md>\d{1,2}\s?月\s?\d{1,2}\s?[日号]?|\d{1,2}[/-]\d{1,2})"
        )

        # 日期范围
        self.date_range = re.compile(
            r"(?P<range_start>[\d年月日号/\\-]+|\b今天\b|\b明天\b|\b后天\b|\b\d+天后\b|\b下周[一二三四五六日天]\b)"
            r"\s*(?:至|到|—|-|–|~|～)\s*"
            r"(?P<range_end>[\d年月日号/\\-]+|\b今天\b|\b明天\b|\b后天\b|\b\d+天后\b|\b下周[一二三四五六日天]\b)"
        )

        # ---------- 相对日期 ----------
        self.relative_date = re.compile(
            r"(?P<rel>(今天|明天|后天|大后天|本周[一二三四五六日天]|下周[一二三四五六日天]|上周[一二三四五六日天]"
            r"|(?:\d+)\s?天(后|以后|前|之前)|(?:\d+)\s?周(后|以后|前|之前)|(?:\d+)\s?个月(后|以后|前|之前)"
            r"|明年|后年|去年|上个月|下个月|下*下个月|本月|本年度|今年))"
        )

        # ---------- 时间 ----------
        self.time_simple = re.compile(
            r"(?P<time>(?:[01]?\d|2[0-3])[:：][0-5]\d(?:\s*[-~到至]\s*(?:[01]?\d|2[0-3])[:：][0-5]\d)?"
            r"|(?:上午|下午|中午|早上|晚上)?\s?(?:[01]?\d|2[0-3])\s?点(?:半|半钟)?(?:\d{1,2}分)?"
            r"|\d{1,2}时(?:\d{1,2}分)?)"
        )

        # ---------- 星期 ----------
        self.weekday = re.compile(
            r"(?P<weekday>(?:每[个]?|本|下|上)?(?:周|星期)[一二三四五六日天]"
            r"|周[一二三四五六日天](?:[、,，]\s*[一二三四五六日天])*(?:到[一二三四五六日天])?)"
        )

        # ---------- 地点 ----------
        self.place_pattern = re.compile(
            r"(?P<place>[\u4e00-\u9fa5A-Za-z0-9··\-\s]{1,40}"
            r"(?:室|馆|厅|楼|中心|公园|大厦|操场|会议室|酒店|咖啡馆|办公室|实验室|教室|礼堂|工厂|车间))"
        )

        # ---------- 人物 ----------
        self.person_pattern = re.compile(
            r"(?P<person>(?:[A-Z][a-z]+|[A-Za-z·\-\s]{2,30}|[\u4e00-\u9fa5]{2,4})"
            r"(?:先生|女士|小姐|老师|博士|教授|经理|同学|同事)?)"
        )

        # ---------- 事件 ----------
        self.event_pattern = re.compile(
            r"(?P<event>开会|会议|培训|讲座|汇报|考试|聚餐|演出|比赛|值班|研讨|组会|出游|面试|签约|验收|例会|晨会|晚会|研修)"
        )

        # ---------- 持续时间 ----------
        self.duration_pattern = re.compile(
            r"(?P<duration>(?:半天|全天|一整天|数小时|[一二三四五六七八九十\d]{1,3}\s?(?:小时|小时钟|h|分钟|分)))"
        )

        # ---------- 周期 / 重复模式 ----------
        self.recurrence_patterns = {
            # 每天 / 每周 / 每月 / 每年
            "basic": re.compile(r"(?P<basic>每(?:天|日|周|月|年|工作日))"),

            # 每周一 / 每周一三五 / 每周一到周五
            "weekday_list": re.compile(
                r"每(?:周|周的|星期)?(?P<days>[一二三四五六日天]"
                r"(?:[、,，]\s*[一二三四五六日天])*(?:[至\-到][一二三四五六日天])?)"
            ),

            # 隔X天 / 每隔X周
            "interval": re.compile(
                r"(?P<interval>(?:每隔|隔)(?P<num>\d+)[\s\-]?(?P<unit>天|日|周|星期|月|年))"
            ),

            # 每N天 / 每N周 / 每N月
            "every_n": re.compile(
                r"每\s?(?P<n>\d+)\s?(?P<unit>天|日|周|月|年)"
            ),

            # 每月第N个周X
            "monthly_nth_weekday": re.compile(
                r"每月第?\s?(?P<n>[一二三四五六七八九十\d]+)个?周(?P<wd>[一二三四五六日天])"
            ),

            # 每月最后一天 / 工作日
            "monthly_last": re.compile(
                r"每月最后(?:一天|日|个工作日)"
            ),

            # 每年X月X日
            "yearly_on": re.compile(
                r"每年(?P<month>\d{1,2})\s?月(?P<day>\d{1,2})\s?[日号]?"
            ),

            # 每周的周一到周五
            "weekday_range": re.compile(
                r"(?:每周的?|周|星期)"
                r"(?P<start>[一二三四五六日天])\s*(?:到|至|—|-|–)\s*(?P<end>[一二三四五六日天])"
            ),
        }

        # ---------- 星期映射 ----------
        self.weekday_map = {
            "一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6
        }

    # ----------------------------------------------------------------------

    def extract_recurrence(self, text: str):
        """提取文本中的周期性重复表达"""
        results = []
        for name, pat in self.recurrence_patterns.items():
            for m in pat.finditer(text):
                info = {"type": name, "match": m.group(0)}
                info.update({k: v for k, v in m.groupdict().items() if v})
                results.append(info)
        return results

    # ----------------------------------------------------------------------

    def parse(self, text: str) -> dict:
        """提取原始事件信息（新增周期性识别）"""
        results = {
            "dates": [m[0] for m in self.date_full.findall(text)],
            "times": [m[0] for m in self.time_simple.findall(text)],
            "weeks": [m[0] for m in self.weekday.findall(text)],
            "places": [m[0] for m in self.place_pattern.findall(text)],
            "persons": [m[0] for m in self.person_pattern.findall(text)],
            "events_extract": [m[0] for m in self.event_pattern.findall(text)],
            "events_full": text.replace("\n", ""),
            "durations": [m[0] for m in self.duration_pattern.findall(text)],
            "recurrences": self.extract_recurrence(text),  # ✅ 新增周期性结果
        }

        return results

    # ----------------------------------------------------------------------

    def resolve_date(self, token: str, base_date: datetime) -> str:
        """将日期表达解析成 YYYY-MM-DD"""
        token = token.strip()

        if re.match(r"\d{4}[年/-]\d{1,2}[月/-]\d{1,2}", token):
            token = token.replace("年", "-").replace("月", "-").replace("日", "").replace(" ", "")
            return token

        if re.match(r"\d{1,2}[月/-]\d{1,2}", token):
            parts = re.split(r"[月/-]", token.replace("日", "").replace(" ", ""))
            return f"{base_date.year}-{int(parts[0]):02d}-{int(parts[1]):02d}"

        if token == "今天": return base_date.strftime("%Y-%m-%d")
        if token == "明天": return (base_date + timedelta(days=1)).strftime("%Y-%m-%d")
        if token == "后天": return (base_date + timedelta(days=2)).strftime("%Y-%m-%d")
        if token == "大后天": return (base_date + timedelta(days=3)).strftime("%Y-%m-%d")

        m = re.match(r"本周([一二三四五六日天])", token)
        if m:
            target = self.weekday_map[m.group(1)]
            delta = (target - base_date.weekday()) % 7
            return (base_date + timedelta(days=delta)).strftime("%Y-%m-%d")

        m = re.match(r"下周([一二三四五六日天])", token)
        if m:
            target = self.weekday_map[m.group(1)]
            delta = 7 + target - base_date.weekday()
            return (base_date + timedelta(days=delta)).strftime("%Y-%m-%d")

        m = re.match(r"(\d+)天(后|以后)", token)
        if m:
            return (base_date + timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")

        m = re.match(r"(\d+)周(后|以后)", token)
        if m:
            return (base_date + timedelta(weeks=int(m.group(1)))).strftime("%Y-%m-%d")

        if token == "下个月":
            return (base_date + relativedelta(months=1)).strftime("%Y-%m-%d")
        if token == "下下个月":
            return (base_date + relativedelta(months=2)).strftime("%Y-%m-%d")

        m = re.match(r"(\d+)个月(后|以后)", token)
        if m:
            return (base_date + relativedelta(months=int(m.group(1)))).strftime("%Y-%m-%d")

        if token == "明年":
            return (base_date + relativedelta(years=1)).strftime("%Y-%m-%d")
        if token == "后年":
            return (base_date + relativedelta(years=2)).strftime("%Y-%m-%d")

        m = re.match(r"(\d+)年(后|以后)", token)
        if m:
            return (base_date + relativedelta(years=int(m.group(1)))).strftime("%Y-%m-%d")

        m = re.match(r"(\d+)号", token)
        if m:
            return f"{base_date.year}-{base_date.month:02d}-{int(m.group(1)):02d}"

        return token

    def resolve_dates(self, tokens: list, base_date: datetime) -> list:
        return [self.resolve_date(tok, base_date) for tok in tokens]

    def process_text(self, text_path):
        """处理文本并解析日期 + 周期信息"""
        text = r(text_path)
        result = self.parse(text)
        base = datetime.today()
        resolved = self.resolve_dates(result["dates"], base)
        result["dates"] = resolved

        for key, value in result.items():
            if value == []:
                result[key] = None
        return {"ner_extract": result}
