import google.generativeai as genai
import json
import os
import asyncio

class GeminiService:
    """
    Google Gemini API를 사용하여 텍스트에서 위치 정보를 비동기적으로 추출하는 서비스입니다.
    """
    def __init__(self, task_instance=None):
        self.task_instance = task_instance
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.prompt_template = """
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

    async def extract_locations_from_transcript(self, transcript: str) -> list:
        """
        Google Gemini API를 사용하여 주어진 텍스트(YouTube 스크립트)에서 장소 이름과 좌표를 비동기적으로 추출합니다.
        
        Args:
            transcript (str): 장소 정보를 추출할 텍스트 스크립트.

        Returns:
            list: 추출된 장소 정보(이름, 위도, 경도)를 담은 딕셔너리 리스트. 
                  장소 추출에 실패하거나 텍스트가 없으면 빈 리스트를 반환합니다.
        """
        if not transcript:
            print("⚠️ 처리할 텍스트가 없어 장소 추출을 건너뜁니다.")
            if self.task_instance:
                self.task_instance.update_state(
                    state='PROGRESS',
                    meta={'current_step': '스크립트 없음. 위치 추출 건너뜀.', 'progress': 70}
                )
            return []

        print("➡️ Gemini API로 장소 및 좌표 추출을 시작합니다. (비동기)")
        
        if self.task_instance:
            self.task_instance.update_state(
                state='PROGRESS',
                meta={'current_step': 'AI 모델을 통한 위치 정보 추출 및 분석 중 (Gemini API 호출)...', 'progress': 45}
            )

        prompt = self.prompt_template.format(transcript=transcript)
        
        response = None
        try:
            response = await self.model.generate_content_async(prompt)
            
            if self.task_instance:
                self.task_instance.update_state(
                    state='PROGRESS',
                    meta={'current_step': 'Gemini API 응답 처리 중...', 'progress': 60}
                )

            result_text = response.text.strip().lstrip('```json').rstrip('```')
            locations = json.loads(result_text)
            print("✅ Gemini 장소 추출 완료.")
            print(locations)
            return locations
        except Exception as e:
            print(f"❌ Gemini API 처리 중 오류 발생: {e}")
            if response:
                print(f"받은 응답: {response.text}")
            if self.task_instance:
                self.task_instance.update_state(
                    state='FAILURE',
                    meta={'current_step': 'AI 분석 실패', 'error_message': str(e)}
                )
            return []