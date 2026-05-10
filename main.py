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

    # 1. 사용 가능한 모델 목록 가져오기 (디스커버리 로직)
    list_url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
    try:
        model_list_res = requests.get(list_url)
        models_data = model_list_res.json()
        
        # 호출 가능한 'gemini' 모델 찾기
        available_models = [m['name'] for m in models_data.get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]
        print(f"--- Available Models: {available_models} ---")
        
        if not available_models:
            return f"ERROR: No available Gemini models found for this key. (Check AI Studio Project)"
        
        # 1.5 flash -> 2.0 flash -> 1.0 pro 순서로 우선순위 검색
        selected_model = ""
        for m in ["models/gemini-1.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-pro"]:
            if m in available_models:
                selected_model = m
                break
        
        if not selected_model: selected_model = available_models[0] # 아무거나 첫 번째 모델 선택
        
        print(f"Selected Model: {selected_model}")
        
        # 2. 선택된 모델로 분석 요청
        gen_url = f"https://generativelanguage.googleapis.com/v1/{selected_model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": f"뉴스 요약 및 영어표현 3개 정리해줘:\n{news_text}"}]}]
        }
        
        response = requests.post(gen_url, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"AI_API_ERROR: {response.status_code} - {response.text}"

    except Exception as e:
        return f"SYSTEM_ERROR: {str(e)}"

def send_telegram(content):
    token = "".join(os.environ.get("TELEGRAM_TOKEN", "").split())
    chat_id = "".join(os.environ.get("TELEGRAM_CHAT_ID", "").split())
    if not token or not chat_id: return
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": content})
    except: pass

def send_email(content):
    user = "".join(os.environ.get("EMAIL_USER", "").split())
    password = "".join(os.environ.get("EMAIL_PASS", "").split())
    msg = MIMEMultipart()
    msg['From'], msg['To'], msg['Subject'] = user, user, "[News Agent] Today's Study"
    msg.attach(MIMEText(content, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, user, msg.as_string())
        server.quit()
        print("Success: Email Sent!")
    except Exception as e: print(f"Email Error: {e}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print(f"Report Result: {report[:100]}...")
        if "ERROR" not in report: # 에러가 아닐 때만 발송
            send_telegram(report)
            send_email(report)
        else:
            print("Skipping send due to AI error.")
            send_email(f"AI 분석 실패 로그:\n{report}") # 실패 원인을 메일로 전송
