import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from scripts.Tools import r, w
from scripts.path_control import PM
from scripts.unique_string_generate import unique_name  # pip install python-dateutil


class NERProcessor:
    def __init__(self):
        """
        命名实体识别（NER）正则初始化：
        主要用于提取文本中的日期、时间、地点、人物、事件、持续时间等实体。
        """

        # -------------------------------
        # 日期模式（支持绝对日期、相对日期、自然语言日期）
        # 示例：
        #   2025年9月30日、2025 年 9 月 30 日、9月30日、明天、下周五、3天后、2个月后、明年 等
        # -------------------------------
        self.date_pattern = re.compile(
            r"("  # 整个日期模式的开始
            r"\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日号]?"           # 2025年9月30日 / 2025-9-30 / 2025/9/30 / 2025年9月30号
            r"|\d{4}\s?年\s?\d{1,2}\s?月\s?\d{1,2}\s?[日号]?"   # 2025 年 9 月 30 日（含空格）
            r"|\d{1,2}[月/-]\d{1,2}[日号]?"                    # 9月30日 / 9-30
            r"|\d{1,2}\s?月\s?\d{1,2}\s?[日号]?"               # 9 月 30 日
            r"|今天|明天|后天|大后天"                       # 口语表达
            r"|本周[一二三四五六日天]"                      # 本周五
            r"|下周[一二三四五六日天]"                      # 下周二
            r"|(\d+)\s?天(后|以后)"                         # 3天后 / 3 天以后
            r"|(\d+)\s?周(后|以后)"                         # 2周后
            r"|下*下个月"                                   # 下个月 / 下下个月
            r"|(\d+)\s?个月(后|以后)"                       # 3个月后
            r"|明年|后年"                                   # 明年、后年
            r"|(\d+)\s?年(后|以后)"                         # 2年后
            r"|(\d+)\s?号"                                # 2号，同一个月的第几天
            r")"  # 整个日期模式的结束
        )

        # -------------------------------
        # 时间模式（支持多种格式）
        # 示例：
        #   14:30、14:30-16:00、下午3点半、9时30分
        # -------------------------------
        self.time_pattern = re.compile(
            r"("  # 开始
            r"\d{1,2}[:：]\d{2}(-\d{1,2}[:：]\d{2})?"       # 14:30 或 14:30-16:00
            r"|(上午|下午)?\s?\d{1,2}\s?点\s?半?"            # 下午3点半、上午10点
            r"|\d{1,2}\s?时\s?(\d{1,2}\s?)?分?"             # 9时30分、15时
            r")"  # 结束
        )

        # -------------------------------
        # 星期模式（星期一 / 周一）
        # -------------------------------
        self.week_pattern = re.compile(r"(星期[一二三四五六日天]|周[一二三四五六日天末])")

        # -------------------------------
        # 地点模式（常见场所名称后缀）
        # -------------------------------
        self.place_pattern = re.compile(
            r"([\u4e00-\u9fa5A-Za-z0-9]+(室|馆|厅|楼|中心|公园|大厦|操场|会议室))"
        )

        # -------------------------------
        # 人物模式（常见称谓）
        # -------------------------------
        self.person_pattern = re.compile(
            r"([\u4e00-\u9fa5]{2,4}(老师|同学|经理|主任|博士|先生|女士)?)"
        )

        # -------------------------------
        # 事件 / 活动模式
        # -------------------------------
        self.event_pattern = re.compile(
            r"(开会|会议|培训|讲座|汇报|考试|聚餐|演出|比赛|值班|研讨)"
        )

        # -------------------------------
        # 持续时间模式（单位：小时 / 分钟 / 天）
        # -------------------------------
        self.duration_pattern = re.compile(
            r"([一二三四五六七八九十\d]{1,2}\s?(小时|分钟)|半天|全天|一整天)"
        )

        # -------------------------------
        # 星期汉字 → 数字映射（周一=0 ... 周日=6）
        # -------------------------------
        self.weekday_map = {
            "一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6
        }

    def parse(self, text: str) -> dict:
        """提取原始事件信息（未解析相对日期）"""
        return {
            "dates": [m[0] if isinstance(m, tuple) else m for m in self.date_pattern.findall(text)],
            "times": [m[0] for m in self.time_pattern.findall(text)],
            "weeks": self.week_pattern.findall(text),
            "places": self.place_pattern.findall(text),
            "persons": self.person_pattern.findall(text),
            "events": self.event_pattern.findall(text),
            "durations": self.duration_pattern.findall(text),
        }

    def resolve_date(self, token: str, base_date: datetime) -> str:
        """将日期表达解析成 YYYY-MM-DD"""
        token = token.strip()

        # ---- 绝对日期 ----
        if re.match(r"\d{4}[年/-]\d{1,2}[月/-]\d{1,2}", token):
            token = token.replace("年", "-").replace("月", "-").replace("日", "").replace(" ", "")
            return token
        if re.match(r"\d{1,2}[月/-]\d{1,2}", token):
            parts = re.split(r"[月/-]", token.replace("日", "").replace(" ", ""))
            return f"{base_date.year}-{int(parts[0]):02d}-{int(parts[1]):02d}"

        # ---- 简单口语 ----
        if token == "今天": return base_date.strftime("%Y-%m-%d")
        if token == "明天": return (base_date + timedelta(days=1)).strftime("%Y-%m-%d")
        if token == "后天": return (base_date + timedelta(days=2)).strftime("%Y-%m-%d")
        if token == "大后天": return (base_date + timedelta(days=3)).strftime("%Y-%m-%d")

        # ---- 周表达 ----
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

        # ---- 相对天数 ----
        m = re.match(r"(\d+)天(后|以后)", token)
        if m:
            return (base_date + timedelta(days=int(m.group(1)))).strftime("%Y-%m-%d")

        # ---- 相对周数 ----
        m = re.match(r"(\d+)周(后|以后)", token)
        if m:
            return (base_date + timedelta(weeks=int(m.group(1)))).strftime("%Y-%m-%d")

        # ---- 月份 ----
        if token == "下个月":
            return (base_date + relativedelta(months=1)).strftime("%Y-%m-%d")
        if token == "下下个月":
            return (base_date + relativedelta(months=2)).strftime("%Y-%m-%d")

        m = re.match(r"(\d+)个月(后|以后)", token)
        if m:
            return (base_date + relativedelta(months=int(m.group(1)))).strftime("%Y-%m-%d")

        # ---- 年份 ----
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

        return token  # fallback

    def resolve_dates(self, tokens: list, base_date: datetime) -> list:
        """批量解析日期表达"""
        return [self.resolve_date(tok, base_date) for tok in tokens]
    

    def full_result(self,result, full_text):
        # if result["events"] == []:
        result["events"] = full_text.split('\n')
        if isinstance(result["events"], list):
            result["events"] = ''.join(result["events"])
        return result

    def process_text(self, text_path):


        text = r(text_path)
        result = self.parse(text)
        base = datetime.today()  # 基准日期
        resolved = self.resolve_dates(result["dates"], base)
        result["dates"] = resolved
        res_txt = self.full_result(result, text)

        return res_txt
