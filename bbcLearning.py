import json
import os
import requests
from bs4 import BeautifulSoup
from scripts.path_control import PM
from scripts.get_date_formate import today
import ijson
from scripts.logger import logger
import urllib.parse

class BbcLearning:
    def __init__(self):
        self.baseurl = "https://www.bbc.co.uk"
        self.Bbc_dir = PM.get_env("BBC_DIR_PATH")
        self.filepath = PM.get_env("BBC_JSON_PATH")
        # self.doing = self.daily_work()
        
    def save_json(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def get_next(self):
        """取出第一个未学习的数据"""
        for item in self.read_json_items():
            if not item.get("learned"):
                return item
        return None

    def read_json_items(self):
        """读取JSON中的所有item"""
        with open(self.filepath, 'r', encoding='utf-8') as f:
            for item in ijson.items(f, 'item'):
                yield item

    def mark_learned(self, item):
        """根据唯一标识在 JSON 中标记已学习"""
        # 需要重新设计这个方法，因为ijson是只读的
        # 建议先读取所有数据，修改后再保存
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for record in data:
            if record.get("href") == item.get("href"):
                record["learned"] = True
                break
        
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def clean_filename(self, url):
        """清理文件名，移除查询参数"""
        filename = os.path.basename(urllib.parse.urlparse(url).path)
        return filename

    def Download(self, url,f):
        filename = self.clean_filename(url)
        folder = today()
        os.makedirs(f, exist_ok=True)
        path = os.path.join(f, filename)
        
        # 如果文件已存在，直接返回路径
        if os.path.exists(path):
            return path
            
        r = requests.get(url)
        r.raise_for_status()
        with open(path, 'wb') as f:
            f.write(r.content)
        return path
    
    def get_link(self, url):
        """
        在页面中搜索：
        1. 一个 <a> 标签，其文本为 "transcript"，获取其 href。
        2. 一个 <a> 标签，其文本为 "Download Audio"，获取其 href。
        返回一个字典，包含两个键：'transcript' 和 'audio'。
        """

        # 请求网页内容
        url = f"{self.baseurl}{url}"
        response = requests.get(url)
        response.raise_for_status()

        # 使用 BeautifulSoup 解析网页
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找文本为 "transcript" 的链接
        link_transcript = None
        a_transcript = soup.find('a', string=lambda s: s and s.strip().lower() == 'transcript')
        if a_transcript and a_transcript.has_attr('href'):
            link_transcript = a_transcript['href']

        # 查找文本为 "Download Audio" 的链接
        link_audio = None
        a_audio = soup.find('a', string=lambda s: s and s.strip().lower() == 'download audio')
        if a_audio and a_audio.has_attr('href'):
            link_audio = a_audio['href']

        return {
            'transcript': link_transcript,
            'audio': link_audio
        }
    
    def write_title(self, f, *list_info):
        folder = today()
        os.makedirs(f, exist_ok=True)
        path = os.path.join(f, "title.txt")
        with open(path, "w", encoding="utf-8") as f:
            for i in list_info:
                f.write(i + "\n")

    def read_title(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()

    def daily_work(self, daily_folder):

        # daily_folder = today()
        daily_folder_path = os.path.join(self.Bbc_dir, daily_folder)
        
        if os.path.exists(daily_folder_path):
            # 判断该路径下是否有mp3文件 and pdf文件
            mp3_files = [f for f in os.listdir(daily_folder_path) if f.endswith('.mp3')]
            pdf_files = [f for f in os.listdir(daily_folder_path) if f.endswith('.pdf')]
            txt_files = [f for f in os.listdir(daily_folder_path) if f.endswith('.txt')]
            
            if mp3_files and pdf_files and txt_files:
                title_path = os.path.join(daily_folder_path, txt_files[0])
                titleinfo = self.read_title(title_path)
                if titleinfo:
                    doing = {
                        "title": titleinfo[0].strip(),
                        "url": titleinfo[1].strip() if len(titleinfo) > 1 else "",
                        "path_audio": os.path.join(daily_folder_path, mp3_files[0]),
                        "path_pdf": os.path.join(daily_folder_path, pdf_files[0]),
                    }
                    return doing
        
        try:
            article = self.get_next()
            if article:
                info = self.get_link(article["href"])  # 修复拼写错误
                path_pdf = None
                path_audio = None
                
                if info["transcript"]:
                    path_pdf = self.Download(info["transcript"],daily_folder_path)
                if info["audio"]:
                    path_audio = self.Download(info["audio"],daily_folder_path)

                # 保存标题信息
                self.write_title(daily_folder_path, article["title"], article["href"])
                
                doing = {
                    "title": article["title"],
                    "url": article["href"],
                    "path_audio": path_audio,
                    "path_pdf": path_pdf
                }
                
                # 标记为已学习
                self.mark_learned(article)
                
                return doing
            else:
                return None
                
        except Exception as e:
            logger.error(f"Daily work error: {e}")
            return None


if __name__ == "__main__":
    bbc = BbcLearning()
    for folder in range(1, 20, 1):
        daily_folder = f"2025-11-{folder:02}"
        x = bbc.daily_work(daily_folder=daily_folder)
        if x:
            print("Download Successfully, into {daily_folder}, title: {title}".format(daily_folder=daily_folder, title=x["title"]))
