import feedparser
import os
import requests
import smtplib
import google.generativeai as genai
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
                news_list.append(f"[{source}] {feed.entries[0].title}")
        except: continue
    return "\n".join(news_list)

def analyze_news(news_text):
    api_key = "".join(os.environ.get("GEMINI_API_KEY", "").split())
    if not api_key: return "Error: API Key Missing"
    
    genai.configure(api_key=api_key)
    
    # 시도해볼 모델 리스트 (우선순위 순)
    model_candidates = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
    
    last_error = ""
    for model_name in model_candidates:
        try:
            print(f"Attempting with model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            prompt = f"다음 뉴스 리스트를 한글로 요약하고 관련 영어 표현 3개를 정리해줘:\n\n{news_text}"
            response = model.generate_content(prompt)
            
            if response and response.text:
                print(f"Success with model: {model_name}")
                return response.text
        except Exception as e:
            last_error = str(e)
            print(f"Model {model_name} failed: {last_error}")
            continue
            
    return f"AI_ERROR: All models failed. Last error: {last_error}"

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
    msg['Subject'] = "[News Agent] Today's English Digest"
    msg.attach(MIMEText(content, 'plain'))

    try:
        # 이전에 성공한 TLS 587 포트 설정을 유지
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, user, msg.as_string())
        server.quit()
        print("Success: Email sent!")
    except Exception as e:
        print(f"Fail: Email error {e}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print(f"Final Report Sample: {report[:100]}")
        send_telegram(report)
        send_email(report)
    else:
        print("No news found.")
