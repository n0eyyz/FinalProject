import google.generativeai as genai
import json
import os

def extract_locations_with_gemini(transcript: str) -> list:
    """
    Gemini API를 사용하여 텍스트에서 장소 이름과 좌표를 추출합니다.
    """
    if not transcript:
        print("⚠️ 처리할 텍스트가 없어 장소 추출을 건너뜁니다.")
        return []

    print("➡️ Gemini API로 장소 및 좌표 추출을 시작합니다.")
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # --- 여기부터가 개선된 영문 프롬프트입니다 ---
    prompt = f"""
    You are an expert AI specializing in analyzing YouTube food vlogs to extract restaurant and cafe names.
    Your task is to identify all the specific names of places like restaurants, cafes, bakeries, and food stalls that the vlogger visits or mentions in the provided script.

    **Instructions:**
    1.  Focus only on specific, proper names of establishments (e.g., "Fengmi Bunsik", "Cafe Waileddeog").
    2.  Exclude general locations like "Yaksu-dong" or "near Yaksu Station" unless they are part of a specific store name. Do not extract addresses.
    3.  Return the results as a JSON array of objects. Each object must contain "name", "lat", and "lng" keys.
    4.  For "lat" and "lng", provide the best available coordinates from Google Maps.
    5.  **If you cannot find the precise coordinates for a place, use `null` for the "lat" and "lng" values.** Do not exclude the location from the list.
    6.  The final output must be only the JSON array, with no other text or explanations.

    **Example:**
    Text: "First, I went to Gold Pâtisserie for some bread, then had lunch at a place called Daehan Gukbap. I also heard about a new place called 'Secret Spot' but couldn't find it."
    Correct Output:
    [
        {{"name": "Gold Pâtisserie", "lat": 37.5, "lng": 127.0}},
        {{"name": "Daehan Gukbap", "lat": 37.5, "lng": 127.0}},
        {{"name": "Secret Spot", "lat": null, "lng": null}}
    ]

    **Now, analyze the following text:**
    ---
    Text: "{transcript}"
    ---
    JSON Result:
    """
    # --- 프롬프트는 여기까지입니다 ---
    
    response = None
    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip().lstrip('```json').rstrip('```')
        locations = json.loads(result_text)
        print("✅ Gemini 장소 추출 완료.")
        print(locations)
        return locations
    except Exception as e:
        print(f"❌ Gemini API 처리 중 오류 발생: {e}")
        if response:
            print(f"받은 응답: {response.text}")
        return []
    
