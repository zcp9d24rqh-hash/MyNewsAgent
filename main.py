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
        "BBC": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "NYT": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"
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
    # 공백 제거 및 API 키 로드
    api_key = "".join(os.environ.get("GEMINI_API_KEY", "").split())
    if not api_key: return "Error: API Key Missing"
    
    try:
        # [핵심] 404 에러 해결을 위해 api_version을 v1beta로 강제 지정합니다.
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Summarize these news in Korean and pick 3 English expressions with examples: {news_data}"
        )
        return response.text
    except Exception as e:
        return f"AI_ERROR: {str(e)}"

def send_telegram(content):
    token = "".join(os.environ.get("TELEGRAM_TOKEN", "").split())
    chat_id = "".join(os.environ.get("TELEGRAM_CHAT_ID", "").split())
    if not token or not chat_id: return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # 특수문자 충돌 방지를 위해 Markdown 대신 일반 텍스트로 안전하게 발송합니다.
    payload = {"chat_id": chat_id, "text": content}
    try:
        requests.post(url, json=payload)
    except: pass

def send_email(content):
    user = "".join(os.environ.get("EMAIL_USER", "").split())
    password = "".join(os.environ.get("EMAIL_PASS", "").split())
    if not user or not password: return

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = user
    msg['Subject'] = "[News Agent] Today's English News Digest"
    msg.attach(MIMEText(content, 'plain'))

    try:
        # 이전 실행에서 성공한 587 포트/TLS 방식을 유지합니다.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, user, msg.as_string())
        server.quit()
        print("Success: Email sent!")
    except Exception as e:
        print(f"Fail: Email error {e}")

if __name__ == "__main__":
    news = fetch_news()
    if news:
        print(f"Found {len(news)} news items. Analyzing...")
        report = analyze_news(news)
        print(f"--- AI Report ---\n{report[:100]}...")
        send_telegram(report)
        send_email(report)
    else:
        print("No news found.")
