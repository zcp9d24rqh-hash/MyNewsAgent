import feedparser
import os
import requests
import smtplib
from google import genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_env_or_raise(key):
    """환경변수가 없으면 즉시 에러를 발생시켜 프로세스를 중단합니다."""
    value = os.environ.get(key, "").strip()
    # 공백 제거 후 16자리(이메일) 또는 긴 문자열(API) 확인
    clean_value = "".join(value.split())
    if not clean_value:
        raise ValueError(f"GitHub Secret [{key}] is MISSING or EMPTY!")
    return clean_value

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

def analyze_news(news_data, api_key):
    try:
        client = genai.Client(api_key=api_key)
        # 404가 계속 나면 모델명을 'gemini-1.5-pro'로 바꿔서 테스트해 볼 가치가 있습니다.
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Summarize in Korean: {news_data}"
        )
        return response.text
    except Exception as e:
        return f"AI_ERROR: {str(e)}"

def send_email(content, user, password):
    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = user
    msg['Subject'] = "[Success] News Agent Report"
    msg.attach(MIMEText(content, 'plain'))

    try:
        # TLS 587 포트가 가장 범용적입니다.
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, user, msg.as_string())
        server.quit()
        print("Email Sent Successfully!")
    except Exception as e:
        print(f"Email Final Fail: {e}")

if __name__ == "__main__":
    try:
        # 실행 시작 전 모든 자격 증명 강제 검증
        api_key = get_env_or_raise("GEMINI_API_KEY")
        tg_token = get_env_or_raise("TELEGRAM_TOKEN")
        tg_id = get_env_or_raise("TELEGRAM_CHAT_ID")
        mail_user = get_env_or_raise("EMAIL_USER")
        mail_pass = get_env_or_raise("EMAIL_PASS")

        news = fetch_news()
        if news:
            report = analyze_news(news, api_key)
            print(f"Report: {report[:50]}...")
            
            # 텔레그램 발송
            requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage", 
                          json={"chat_id": tg_id, "text": report})
            
            # 이메일 발송
            send_email(report, mail_user, mail_pass)
            
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        exit(1) # GitHub Actions에서 실패로 표시되게 함
