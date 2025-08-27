import json
import os
import re
import google.generativeai as genai
import asyncio

# Google Maps 검증 서비스 임포트
from app.services.maps_verifier import GoogleMapsVerifier, LocationInfo


class GeminiService:
    """
    Google Gemini API를 사용하여 텍스트에서 위치 정보를 추출하고,
    Google Maps API로 검증까지 완료하는 서비스입니다.
    """

    def __init__(self):
        # 프롬프트 내 예시 JSON의 중괄호를 {{, }}로 이스케이프 처리
        self.prompt_template = """You are an expert AI specializing in analyzing YouTube food vlogs to extract restaurant and cafe names.
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
        self.region_prompt_template = """From the following text, identify the primary city or metropolitan area that is the main setting.
Respond with only the name of the city and province/state (e.g., "Suwon, Gyeonggi-do", "Seoul").
Do not add any other explanatory text.

Text: "{transcript}"
Region: """
        # Google Maps 검증기 인스턴스 생성
        self.verifier = GoogleMapsVerifier()

    async def _extract_region_from_transcript(self, transcript: str) -> str | None:
        """스크립트에서 주요 지역(도시) 컨텍스트를 추출합니다."""
        print("➡️ 영상의 주요 지역 컨텍스트 추출을 시작합니다.")
        try:
            prompt = self.region_prompt_template.format(transcript=transcript)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await model.generate_content_async(prompt)
            if response.text:
                region = response.text.strip()
                print(f"✅ 주요 지역으로 '{region}'을 추출했습니다.")
                return region
            return None
        except Exception as e:
            print(f"⚠️ 지역 컨텍스트 추출 중 오류 발생: {e}")
            return None

    async def extract_locations_from_transcript(self, transcript: str) -> list:
        """
        스크립트에서 위치 후보를 추출하고 Google Maps로 검증한 후,
        최종 확인된 장소 목록을 반환합니다.
        """
        if not transcript:
            print("⚠️ 처리할 텍스트가 없어 장소 추출을 건너뜁니다.")
            return []

        # 1. 주요 지역 컨텍스트 추출
        region = await self._extract_region_from_transcript(transcript)

        # 2. Gemini API를 통해 장소 후보 목록 추출
        print("➡️ Gemini API로 장소 후보 추출을 시작합니다.")
        prompt = self.prompt_template.format(transcript=transcript)

        model_name = "gemini-1.5-flash"
        model = genai.GenerativeModel(model_name)
        response = None
        try:
            response = await model.generate_content_async(prompt)

            if hasattr(response, "text") and response.text:
                result_text = response.text.strip().lstrip("```json").rstrip("```")
                # JSON 파싱 전, 불필요한 후행 쉼표 제거
                result_text = re.sub(r",\s*([\}\]])", r"\1", result_text)
                candidate_locations = json.loads(result_text)
                print(
                    f"✅ Gemini가 {len(candidate_locations)}개의 장소 후보를 추출했습니다."
                )
            else:
                print("❌ Gemini 응답에서 텍스트를 찾을 수 없습니다.")
                return []

        except Exception as e:
            print(f"❌ Gemini API 처리 중 오류 발생: {e}")
            if response:
                print(f"받은 응답: {response.text}")
            return []

        # 3. Google Maps API로 검증
        if not candidate_locations:
            return []

        print(f"➡️ Google Maps로 후보 장소 검증을 시작합니다. (지역: {region or 'N/A'})")
        locations_to_verify = [
            LocationInfo(name=loc.get("name"), lat=loc.get("lat"), lng=loc.get("lng"))
            for loc in candidate_locations
            if loc.get("name")
        ]

        verified_locations_info = await self.verifier.verify_locations_batch(
            locations_to_verify, region_context=region
        )

        # 최종 결과를 딕셔너리 리스트로 변환
        final_locations = [loc.to_dict() for loc in verified_locations_info]

        print(f"✅ 검증 완료. 최종 {len(final_locations)}개의 장소가 확인되었습니다.")
        return final_locations
