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
    if not api_key:
        return "Error: API Key is missing."

    client = genai.Client(api_key=api_key)

    try:
        # [진단] 사용 가능한 모델 목록을 확인하여 로그에 남깁니다.
        print("--- Available Models List ---")
        models = client.models.list()
        available_model_names = [m.name for m in models]
        for name in available_model_names:
            print(f"- {name}")
        
        # 목록에 있는 모델 중 하나를 선택 (없으면 기본값 사용)
        target_model = "gemini-1.5-flash"
        if f"models/{target_model}" in available_model_names:
            target_model = f"models/{target_model}"
        elif "gemini-1.5-flash-latest" in available_model_names:
            target_model = "gemini-1.5-flash-latest"

        print(f"Using model: {target_model}")

        response = client.models.generate_content(
            model=target_model,
            contents=f"다음 뉴스를 한글로 요약하고 영어 표현 3개를 뽑아줘: {news_data}"
        )
        return response.text
    except Exception as e:
        return f"AI_ERROR: {str(e)}"

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
        # TLS 587 포트가 자동화 환경에서 보안 연결에 더 유리합니다.
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
        report = analyze_news(news)
        print(f"Final Report Sample: {report[:100]}")
        send_telegram(report)
        send_email(report)
    else:
        print("No news to process.")
