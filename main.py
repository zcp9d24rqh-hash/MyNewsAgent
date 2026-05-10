import feedparser
import os
import requests
import smtplib
from google import genai # 최신 SDK 임포트 방식
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def fetch_news():
    RSS_FEEDS = {
        "CNBC_Biz": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "BBC_World": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "NYT_Tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "CNN_Top": "http://rss.cnn.com/rss/edition.rss"
    }
    news_list = []
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:1]:
            news_list.append({"source": source, "title": entry.title, "link": entry.link})
    return news_list

def analyze_news(news_data):
    # 최신 SDK 클라이언트 생성
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    prompt = f"""
    당신은 전문 영어 학습 큐레이터입니다. 아래 뉴스 데이터를 바탕으로 한글 요약과 영어 학습 자료를 만드세요.
    
    [출력 형식]
    - 각 뉴스별 [매체명]과 [제목]을 적을 것.
    - 한국어 요약 2문장을 작성할 것.
    - 원어민이 즐겨 쓰는 핵심 표현 3개를 선정하여 [표현 - 뜻 - 예문]을 정리할 것.
    - 마크다운(Markdown) 형식을 유지할 것.

    뉴스 데이터: {news_data}
    """
    
    # 모델 호출 방식 변경 (gemini-2.0-flash 권장)
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt
    )
    return response.text

def send_telegram(content):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": content, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def send_email(content):
    sender = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASS"]
    receiver = sender

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = "[Daily Digest] 오늘의 영어 스터디 뉴스가 도착했습니다."
    msg.attach(MIMEText(content, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
    except Exception as e:
        print(f"Email Error: {e}")

if __name__ == "__main__":
    news = fetch_news()
    if news:
        result = analyze_news(news)
        send_telegram(result)
        send_email(result)
    else:
        print("뉴스 데이터를 가져오지 못했습니다.")
