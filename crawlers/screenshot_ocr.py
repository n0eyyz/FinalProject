import easyocr
import pyautogui
import os

# OCR 엔진 미리 준비 (속도 빠름)
reader = easyocr.Reader(['ko', 'en'])


def capture_and_ocr():
    """
    화면 캡처 후 OCR로 텍스트 리스트 추출
    """
    screenshot = pyautogui.screenshot()
    temp_filename = "screen_temp.png"
    screenshot.save(temp_filename)

    results = reader.readtext(temp_filename)
    texts = [item[1] for item in results if len(item[1]) > 1]
    os.remove(temp_filename)
    return texts
