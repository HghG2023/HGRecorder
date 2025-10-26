import re
from typing import List
from .BaseExtractor import BaseExtractor

class EventExtractor(BaseExtractor):
    """提取文本中表示事件、活动、任务的短语（适合学生与自由职业者）"""
    name = "events_extract"

    def __init__(self):
        # 书面表达 + 口语表达 + 常见日常活动
        self.pattern = re.compile(
            r'(?P<event>'
            # 学生常见事件
            r'(上课|听课|考试|测验|考核|交作业|写作业|完成论文|论文提交|开题报告|答辩|实习|选课|放假|军训|'
            r'毕业典礼|班会|学术报告|讲座|演讲|社团活动|晚会|招新|辅导|培训|自习|学习|复习|考试周)'
            r'|'
            # 自由职业/工作类事件
            r'(会议|开会|视频会|电话会|项目|项目启动|项目交付|验收|对接|提交报告|谈合作|签合同|'
            r'出差|出外勤|客户拜访|客户沟通|面试|拍摄|剪片|写稿|发稿|直播|录制|设计|约客户|汇报|讨论)'
            r'|'
            # 生活/社交类事件
            r'(聚会|聚餐|请客|吃饭|约饭|喝酒|唱歌|KTV|旅游|出游|旅行|徒步|爬山|锻炼|跑步|健身|看电影|追剧|打游戏|'
            r'看展|逛街|购物|理发|体检|看病|搬家|装修|约会|见朋友|探亲|走亲戚|接人|送人|'
            r'庆祝|生日|纪念日|婚礼|葬礼|参加典礼|订婚|结婚)'
            r')',
            re.U
        )

    def extract(self, text: str) -> List[str]:
        """从文本中提取所有事件短语"""
        events = [m.group("event").strip() for m in self.pattern.finditer(text)]
        # 去重保持顺序
        return list(dict.fromkeys(events))
