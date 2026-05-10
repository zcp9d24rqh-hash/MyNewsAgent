import feedparser
import os
import requests
import smtplib
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. 뉴스 수집 (주요 외신 RSS)
def fetch_news():
    RSS_FEEDS = {
        "CNBC_Biz": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "BBC_World": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "NYT_Tech": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "CNN_Top": "http://rss.cnn.com/rss/edition.rss"
    }
    news_list = []
    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:1]: # 매체별 최신 기사 1개씩
            news_list.append({"source": source, "title": entry.title, "link": entry.link})
    return news_list

# 2. AI 분석 (Gemini 1.5 Flash 모델 활용)
def analyze_news(news_data):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    당신은 전문 영어 학습 큐레이터입니다. 아래 뉴스 데이터를 바탕으로 한글 요약과 영어 학습 자료를 만드세요.
    
    [출력 형식]
    - 각 뉴스별 [매체명]과 [제목]을 적을 것.
    - 한국어 요약 2문장을 작성할 것.
    - 원어민이 즐겨 쓰는 핵심 표현 3개를 선정하여 [표현 - 뜻 - 예문]을 정리할 것.
    - 마크다운(Markdown) 형식을 유지할 것.

    뉴스 데이터: {news_data}
    """
    response = model.generate_content(prompt)
    return response.text

# 3. 텔레그램 발송
def send_telegram(content):
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": content, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

# 4. 이메일 발송
def send_email(content):
    sender = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASS"]
    receiver = sender # 본인에게 발송

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = "[Daily Digest] 오늘의 영어 스터디 뉴스가 도착했습니다."
    msg.attach(MIMEText(content, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
    except Exception as e:
        print(f"Email Error: {e}")

if __name__ == "__main__":
    # 실행 흐름: 수집 -> 분석 -> 발송
    news = fetch_news()
    if news:
        result = analyze_news(news)
        send_telegram(result)
        send_email(result)
    else:
        print("뉴스 데이터를 가져오지 못했습니다.")
