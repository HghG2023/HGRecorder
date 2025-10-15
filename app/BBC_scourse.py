
import json
import requests
from bs4 import BeautifulSoup

url = "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english"

r = requests.get(url)
htmlContent = r.content
soup = BeautifulSoup(htmlContent, 'html.parser')
content= soup.find_all('div', {'class':'text'})
with open("res.json", 'w', encoding="utf-8") as f:
    # num : [contenttext,contentherf]
    json.dump([{"title":item.a.text, "href":item.a['href']} for index, item in enumerate(content)], f, ensure_ascii=False, indent=4)

# def DownloadPDF(url, path):
#     r = requests.get(url)
#     with open(path, 'wb') as f:
#         f.write(r.content)

# def DownloadAudio(url, path):
#     r = requests.get(url)
#     with open(path, 'wb') as f:
#         f.write(r.content)

# pdf_url = "https://downloads.bbc.co.uk/learningenglish/features/6min/251002_6_minute_english_have_you_ever_seen_a_whale_transcript.pdf"
# audio_url = "https://downloads.bbc.co.uk/learningenglish/features/6min/251002_6_minute_english_have_you_ever_seen_a_whale_download.mp3"

# DownloadPDF(pdf_url, 'BBC_scourse.pdf')
# DownloadAudio(audio_url, 'BBC_scourse.mp3')