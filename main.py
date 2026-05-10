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
    # .strip()을 통해 혹시 모를 공백을 완전히 제거합니다.
    raw_key = os.environ.get("GEMINI_API_KEY", "")
    api_key = "".join(raw_key.split()) # 모든 공백 제거
    
    if not api_key: return "Error: API Key Missing"
    
    try:
        client = genai.Client(api_key=api_key)
        # 모델명을 가장 단순한 문자열로 전달합니다.
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Summarize these news in Korean and pick 3 English expressions: {news_data}"
        )
        return response.text
    except Exception as e:
        return f"AI_ERROR: {str(e)}"

def send_telegram(content):
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": content})

def send_email(content):
    user = os.environ.get("EMAIL_USER", "").strip()
    # 앱 비밀번호 16자리는 공백이 절대 없어야 합니다.
    raw_pw = os.environ.get("EMAIL_PASS", "")
    password = "".join(raw_pw.split()) 
    
    if not user or not password: return

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = user
    msg['Subject'] = "[News Agent] Daily English Study"
    msg.attach(MIMEText(content, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.sendmail(user, user, msg.as_string())
        print("Success: Email sent!")
    except Exception as e:
        print(f"Fail: Email error {e}")

if __name__ == "__main__":
    news = fetch_news()
    if news:
        report = analyze_news(news)
        print(f"Report: {report[:100]}...")
        send_telegram(report)
        send_email(report)
