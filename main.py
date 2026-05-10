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
    # 공백 제거 및 환경변수 로드
    raw_key = os.environ.get("GEMINI_API_KEY", "")
    api_key = "".join(raw_key.split())
    
    if not api_key: return "ERROR: API KEY IS EMPTY"

    try:
        # [핵심 수정] API 버전을 v1으로 강제 지정하여 v1beta 404 이슈 해결
        genai.configure(api_key=api_key, transport='rest')
        
        # 모델 객체 생성 (접두사 없이 이름만 사용)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"Summarize these news in Korean and pick 3 English expressions:\n\n{news_text}"
        
        # 콘텐츠 생성 시도
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text
        return "ERROR: AI Response is empty."
        
    except Exception as e:
        # 에러 발생 시 상세 메시지 반환
        return f"AI_ERROR_DETAIL: {str(e)}"

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
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, user, msg.as_string())
        server.quit()
        print("Final Success: Email Sent!")
    except Exception as e:
        print(f"Final Fail: Email error {e}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print(f"Generated Content: {report[:100]}...")
        send_telegram(report)
        send_email(report)
    else:
        print("No news entries found.")
