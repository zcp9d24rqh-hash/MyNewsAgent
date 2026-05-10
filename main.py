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

def analyze_news_rest(news_data):
    """SDK를 쓰지 않고 직접 REST API를 호출하여 404 에러를 우회합니다."""
    api_key = "".join(os.environ.get("GEMINI_API_KEY", "").split())
    if not api_key: return "Error: API Key Missing"
    
    # Google AI REST API 엔드포인트 (v1 버전 사용)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Summarize these news in Korean and pick 3 useful English expressions with examples: {news_data}"
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        res_json = response.json()
        
        # 정상 응답 처리
        if response.status_code == 200:
            return res_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"AI_REST_ERROR ({response.status_code}): {res_json.get('error', {}).get('message', 'Unknown Error')}"
    except Exception as e:
        return f"AI_CONNECTION_ERROR: {str(e)}"

def send_telegram(content):
    token = "".join(os.environ.get("TELEGRAM_TOKEN", "").split())
    chat_id = "".join(os.environ.get("TELEGRAM_CHAT_ID", "").split())
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": content})

def send_email(content):
    user = "".join(os.environ.get("EMAIL_USER", "").split())
    password = "".join(os.environ.get("EMAIL_PASS", "").split())
    
    if not user or not password: return

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = user
    msg['Subject'] = "[News Agent] Daily English Study"
    msg.attach(MIMEText(content, 'plain'))

    try:
        # 이미 성공한 587/TLS 방식 유지
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
        # 신규 REST API 방식 호출
        report = analyze_news_rest(news)
        print(f"Report: {report[:100]}...")
        send_telegram(report)
        send_email(report)
    else:
        print("No news fetched.")
