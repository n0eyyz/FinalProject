from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

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
