import feedparser
import os
import requests
import smtplib
import json
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
                news_list.append(f"[{source}] {feed.entries[0].title}")
        except: continue
    return "\n".join(news_list)

def analyze_news(news_text):
    # API 키에서 공백 제거
    api_key = "".join(os.environ.get("GEMINI_API_KEY", "").split())
    if not api_key: return "ERROR: API KEY IS EMPTY"

    # SDK 대신 직접 REST API URL 사용 (v1 버전 강제)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"다음 뉴스를 한글로 요약하고 영어 표현 3개를 정리해줘:\n\n{news_text}"
            }]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()
        
        # 정상 응답 처리
        if response.status_code == 200:
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"AI_API_ERROR: {response.status_code} - {result.get('error', {}).get('message', 'Unknown Error')}"
    except Exception as e:
        return f"REQUEST_ERROR: {str(e)}"

def send_telegram(content):
    token = "".join(os.environ.get("TELEGRAM_TOKEN", "").split())
    chat_id = "".join(os.environ.get("TELEGRAM_CHAT_ID", "").split())
    if not token or not chat_id: return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": content})
    except: pass

def send_email(content):
    user = "".join(os.environ.get("EMAIL_USER", "").split())
    password = "".join(os.environ.get("EMAIL_PASS", "").split())
    if not user or not password: return

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = user
    msg['Subject'] = "[Daily News] 오늘의 영어 뉴스 요약"
    msg.attach(MIMEText(content, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, user, msg.as_string())
        server.quit()
        print("Success: Email Sent!")
    except Exception as e:
        print(f"Email Error: {e}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print(f"Result: {report[:100]}...")
        send_telegram(report)
        send_email(report)
    else:
        print("No news found.")
