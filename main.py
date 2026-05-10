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
    api_key = "".join(os.environ.get("GEMINI_API_KEY", "").split())
    if not api_key: return "ERROR: API KEY IS EMPTY"

    # 시도할 API 버전과 모델 조합 리스트
    endpoints = [
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash-latest"),
        ("v1", "gemini-1.5-flash-latest")
    ]

    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": f"다음 뉴스를 한글로 요약하고 영어 표현 3개를 정리해줘:\n\n{news_text}"}]}]
    }

    for version, model in endpoints:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
        try:
            print(f"Trying: {version} / {model}...")
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success with {version}/{model}!")
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"❌ Failed {version}/{model}: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Error on {version}/{model}: {str(e)}")
            continue

    return "AI_ERROR: All API combinations failed. Please check if your API Key is active at AI Studio."

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
    msg['Subject'] = "[News Agent] 오늘의 영어 뉴스 요약"
    msg.attach(MIMEText(content, 'plain'))

    try:
        # 이미 검증된 587 포트 설정을 그대로 유지합니다.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, user, msg.as_string())
        server.quit()
        print("Final Success: Email Sent!")
    except Exception as e:
        print(f"Email Error: {e}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print(f"Content Length: {len(report)} characters")
        send_telegram(report)
        send_email(report)
    else:
        print("No news found.")
