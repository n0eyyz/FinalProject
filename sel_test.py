# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# import time
# from pydantic import BaseModel

# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# def extract_instagram_text(post_url: str, headless: bool = True) -> str:
#     # 크롬 옵션 세팅
#     chrome_options = Options()
#     if headless:
#         chrome_options.add_argument("--headless")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--lang=ko_KR")

#     # 드라이버 실행 (chromedriver.exe가 PATH에 있거나, 경로 지정 필요)
#     driver = None
#     try:
#         driver = webdriver.Chrome(options=chrome_options)
#         driver.get(post_url)
#         time.sleep(1)  # 페이지 로딩 대기

#         # 더보기 버튼 클릭(있을 때만)
#         try:
#             more_btn = driver.find_element(By.XPATH, "//span[text()='더 보기']")
#             more_btn.click()
#             time.sleep(1)
#         except Exception:
#             pass  # 더보기 없으면 무시

#         # 게시글 본문 추출 (가장 긴 텍스트 블록을 우선)
#         text_candidates = []
#         try:
#             article = driver.find_element(By.TAG_NAME, "article")
#             # 주로 span/div에 본문 있음, 너무 짧은 건 제외
#             blocks = article.find_elements(By.XPATH, ".//div | .//span")
#             for b in blocks:
#                 t = b.text.strip()
#                 if len(t) > 10 and t not in text_candidates:
#                     text_candidates.append(t)
#         except Exception as e:
#             # Fallback: 전체에서 가장 긴 텍스트 찾기
#             spans = driver.find_elements(By.TAG_NAME, "span")
#             for b in spans:
#                 t = b.text.strip()
#                 if len(t) > 10 and t not in text_candidates:
#                     text_candidates.append(t)

#         # 가장 긴 텍스트를 반환(여러 블록일 경우 \n로 이어붙임)
#         post_fulltext = "\n".join(text_candidates)
#         if not post_fulltext:
#             post_fulltext = "(본문을 찾을 수 없습니다)"
#         return post_fulltext

#     except Exception as e:
#         return f"(에러: {str(e)})"
#     finally:
#         if driver:
#             driver.quit()


# class InstagramUrlRequest(BaseModel):
#     url: str

# @app.post("/extract-instagram")
# async def extract_instagram(data: InstagramUrlRequest):
#     url = data.url
#     # url 유효성 체크 생략
#     # 본문 추출 함수 호출 및 반환
#     text = extract_instagram_text(url)
#     return JSONResponse({"text": text})



#### 중복제거 코드 (작업중) ####

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from pydantic import BaseModel
from urllib.parse import urlparse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def extract_instagram_text(post_url: str) -> str:
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 테스트 시 꺼두기
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--lang=ko_KR")
    chrome_options.add_argument("user-agent=Mozilla/5.0 ...")
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        print(f"[STEP 1] URL 접근: {post_url}")
        driver.get(post_url)
        time.sleep(2)
        
        # 로그인 팝업 닫기
        try:
            close_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='닫기']"))
            )
            driver.execute_script("arguments[0].click();", close_btn)
            print("[STEP 2] 팝업 닫기 성공")
        except Exception as e:
            print("[STEP 2] 팝업 닫기 없음/실패", e)
        
        # '더 보기' 클릭
        try:
            more_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='더 보기']"))
            )
            more_btn.click()
            print("[STEP 3] '더 보기' 클릭 성공")
            time.sleep(1)
        except Exception as e:
            print("[STEP 3] '더 보기' 버튼 없음/실패", e)
        
        # main/h1/div/span에서 추출
        try:
            main = driver.find_element(By.TAG_NAME, "main")
            print("[STEP 4] main 찾음")
            try:
                h1 = main.find_element(By.TAG_NAME, "h1")
                print(f"[STEP 5] h1에서 본문 추출: {h1.text[:100]}")
                return h1.text.strip()
            except Exception as e:
                print("[STEP 5] h1 본문 없음", e)
        except Exception as e:
            print("[STEP 4] main 없음", e)
        
        # Fallback: meta 태그에서 본문 추출
        metas = driver.find_elements(By.TAG_NAME, "meta")
        for m in metas:
            name = m.get_attribute("name") or m.get_attribute("property")
            if name in ["og:description", "description"]:
                content = m.get_attribute("content")
                if content and len(content) > 10:
                    print(f"[STEP 6] meta {name}에서 본문 추출: {content[:100]}")
                    return content.strip()
        
        print("[STEP 7] 본문 추출 실패 (main/h1/meta 모두 없음)")
        return "(본문을 찾을 수 없습니다)"
    finally:
        driver.quit()

# 디버깅용 - 실패 시 html 저장
def _save_debug_page(driver, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"🔍 디버깅용 페이지 소스를 {filename}로 저장했습니다.")
    except Exception:
        pass

class InstagramUrlRequest(BaseModel):
    url: str

@app.post("/extract-instagram")
async def extract_instagram(data: InstagramUrlRequest):
    url = data.url
    if not url or "instagram.com/p/" not in url:
        return JSONResponse(status_code=400, content={"error": "유효한 인스타그램 게시물 URL을 입력해주세요."})
    
    text = extract_instagram_text(url)
    return JSONResponse({"text": text})
