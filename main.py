import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 수집하고 싶은 뉴스 RSS 주소
NEWS_FEEDS = {
    "CNBC Business": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "BBC World": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "NYT Technology": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"
}

def get_latest_news():
    digest = ""
    for source, url in NEWS_FEEDS.items():
        feed = feedparser.parse(url)
        # 각 소스에서 최신 기사 1개씩만 가져오기
        entry = feed.entries[0]
        digest += f"[{source}] {entry.title}\n{entry.link}\n\n"
    return digest

def send_email(content):
    # 이 부분은 GitHub Secrets에서 환경변수로 불러옵니다.
    # 자세한 설정은 아래 3단계를 참고하세요.
    pass

if __name__ == "__main__":
    news_content = get_latest_news()
    print(news_content) # 우선 실행 확인용
