import feedparser
import os
import requests
import smtplib
from google import genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. 뉴스 수집
def fetch_news():
    RSS_FEEDS = {
        "CNBC_Biz": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "BBC_World": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "NYT_Tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "CNN_Top": "http://rss.cnn.com/rss/edition.rss"
    }
    news_list = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:1]:
                news_list.append({"source": source, "title": entry.title, "link": entry.link})
        except Exception as e:
            print(f"Feed Error ({source}): {e}")
    return news_list

# 2. AI 분석 (가장 안정적인 1.5-flash 모델 사용)
def analyze_news(news_data):
    # API 키 확인
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY is missing in Secrets."
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    당신은 전문 영어 학습 큐레이터입니다. 아래 뉴스 데이터를 바탕으로 자료를 만드세요.
    - 각 뉴스별 [매체명]과 [제목] 적기.
    - 한국어 요약 2문장.
    - 원어민 핵심 표현 3개 [표현 - 뜻 - 예문] 정리.
    - 마크다운 형식을 유지할 것.

    뉴스 데이터: {news_data}
    """
    
    try:
        # 모델 명칭을 가장 표준적인 'gemini-1.5-flash'로 고정
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"AI Analysis Error: {str(e)}"

# 3. 텔레그램 발송
def send_telegram(content):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram Secrets missing.")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": content, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Send Error: {e}")

# 4. 이메일 발송
def send_email(content):
    sender = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    if not sender or not password:
        print("Email Secrets missing.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = sender
    msg['Subject'] = "[Daily Digest] 오늘의 영어 스터디 뉴스"
    msg.attach(MIMEText(content, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, sender, msg.as_string())
    except Exception as e:
        print(f"Email Send Error: {e}")

if __name__ == "__main__":
    news = fetch_news()
    if news:
        result = analyze_news(news)
        print("--- Analysis Result ---")
        print(result)
        send_telegram(result)
        send_email(result)
    else:
        print("No news data fetched.")
