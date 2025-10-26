import re
from typing import List
from .BaseExtractor import BaseExtractor

class RecurrenceExtractor(BaseExtractor):
    name = "recurrences"

    def __init__(self):
        # 匹配常见周期 + 可选次数 + 口语表达
        self.pattern = re.compile(
            r'(?P<recurrence>'
            r'每(天|日|周|星期|月|年)'                  # 每天、每周、每月、每年
            r'(?:[一二三四五六七八九十\d]+次|一次|二次|三次|四次|五次)?|'  # 可带次数
            r'每(周一|周二|周三|周四|周五|周六|周日)'  # 每周具体某天
            r'(?:[一二三四五六七八九十\d]+次)?|'        # 可带次数
            r'每(个)?星期(一|二|三|四|五|六|日)'       # 每个星期几
            r'(?:[一二三四五六七八九十\d]+次)?|'        # 可带次数
            r'隔天|隔日|隔周|隔月|隔年|'                 # 间隔表达
            r'每([一二三四五六七八九十\d]+)天|每([一二三四五六七八九十\d]+)周|每([一二三四五六七八九十\d]+)月|每([一二三四五六七八九十\d]+)年|' # 每X天/周/月/年
            r'每天一次|每周一次|每月一次|每年一次|'    # 每次表达
            r'每天下午|每周下午|每月下午|每年下午'     # 口语化时间段
            r')',
            re.U
        )

    def extract(self, text: str) -> List[str]:
        return [m.group("recurrence") for m in self.pattern.finditer(text)]

