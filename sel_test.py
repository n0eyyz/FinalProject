from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_instagram_text(post_url: str, headless: bool = True) -> str:
    # 크롬 옵션 세팅
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=ko_KR")

    # 드라이버 실행 (chromedriver.exe가 PATH에 있거나, 경로 지정 필요)
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(post_url)
        time.sleep(3)  # 페이지 로딩 대기

        # 더보기 버튼 클릭(있을 때만)
        try:
            more_btn = driver.find_element(By.XPATH, "//span[text()='더 보기']")
            more_btn.click()
            time.sleep(1)
        except Exception:
            pass  # 더보기 없으면 무시

        # 게시글 본문 추출 (가장 긴 텍스트 블록을 우선)
        text_candidates = []
        try:
            article = driver.find_element(By.TAG_NAME, "article")
            # 주로 span/div에 본문 있음, 너무 짧은 건 제외
            blocks = article.find_elements(By.XPATH, ".//div | .//span")
            for b in blocks:
                t = b.text.strip()
                if len(t) > 10 and t not in text_candidates:
                    text_candidates.append(t)
        except Exception as e:
            # Fallback: 전체에서 가장 긴 텍스트 찾기
            spans = driver.find_elements(By.TAG_NAME, "span")
            for b in spans:
                t = b.text.strip()
                if len(t) > 10 and t not in text_candidates:
                    text_candidates.append(t)

        # 가장 긴 텍스트를 반환(여러 블록일 경우 \n로 이어붙임)
        post_fulltext = "\n".join(text_candidates)
        if not post_fulltext:
            post_fulltext = "(본문을 찾을 수 없습니다)"
        return post_fulltext

    except Exception as e:
        return f"(에러: {str(e)})"
    finally:
        if driver:
            driver.quit()


class InstagramUrlRequest(BaseModel):
    url: str

@app.post("/extract-instagram")
async def extract_instagram(data: InstagramUrlRequest):
    url = data.url
    # url 유효성 체크 생략
    # 본문 추출 함수 호출 및 반환
    text = extract_instagram_text(url)
    return JSONResponse({"text": text})

