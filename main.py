import feedparser
import os
import requests
import smtplib
from google import genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def fetch_news():
    RSS_FEEDS = {
        "CNBC": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "BBC": "http://feeds.bbci.co.uk/news/world/rss.xml"
    }
    news_list = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                news_list.append({"source": source, "title": feed.entries[0].title, "link": feed.entries[0].link})
        except: continue
    return news_list

def analyze_news(news_data):
    # 공백 제거 및 키 로드
    api_key = "".join(os.environ.get("GEMINI_API_KEY", "").split())
    if not api_key: return "Error: Gemini API Key is missing."
    
    try:
        # 클라이언트 초기화 시 vertex_ai=False를 명시하여 일반 API 모드로 고정
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
        
        # 모델 명칭을 리스트 형태로 시도 (가장 호환성 높은 명칭)
        model_name = "gemini-1.5-flash"
        
        response = client.models.generate_content(
            model=model_name,
            contents=f"Summarize these news in Korean and pick 3 English expressions: {news_data}"
        )
        
        if not response or not response.text:
            return "Error: AI generated an empty response."
        return response.text

    except Exception as e:
        # 상세 에러 로그 출력
        error_msg = str(e)
        print(f"Detailed AI Error: {error_msg}")
        return f"AI Analysis Failed: {error_msg}\n(Check if your API Key has access to {model_name})"

def send_telegram(content):
    token = "".join(os.environ.get("TELEGRAM_TOKEN", "").split())
    chat_id = "".join(os.environ.get("TELEGRAM_CHAT_ID", "").split())
    if not token or not chat_id: return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": content})
    except: pass

def send_email(content):
    user = "".join(os.environ.get("EMAIL_USER", "").split())
    password = "".join(os.environ.get("EMAIL_PASS", "").split())
    if not user or not password: return

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = user
    msg['Subject'] = "[News Agent] Today's Study"
    msg.attach(MIMEText(content, 'plain'))

    try:
        # TLS 587 포트가 자동화 환경에서 가장 안정적입니다.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, user, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Email Error: {e}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        send_telegram(report)
        send_email(report)
    else:
        print("No news to process.")
