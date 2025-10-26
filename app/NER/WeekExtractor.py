
import re
from .BaseExtractor import BaseExtractor


class WeekExtractor(BaseExtractor):
    name = "weeks"

    def __init__(self):
        self.pattern = re.compile(r'(?P<week>周[一二三四五六日天])', re.U)

    def extract(self, text: str):
        return [m.group("week") for m in self.pattern.finditer(text)]
