import os
import googlemaps
import asyncio
import math
from typing import List, Optional, Dict
from dataclasses import dataclass

# .env 파일에서 API 키 로드
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

@dataclass
class LocationInfo:
    """검증 과정에서 사용될 위치 정보를 담는 데이터 클래스"""
    name: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    confidence: float = 1.0  # Gemini 결과에 대한 기본 신뢰도
    source: str = "gemini"
    verified: bool = False
    place_id: Optional[str] = None
    formatted_address: Optional[str] = None
    google_rating: Optional[float] = None
    place_types: Optional[List[str]] = None

    def to_dict(self) -> dict:
        """DB 저장 및 API 응답을 위한 딕셔너리 변환"""
        return {
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
        }

@dataclass
class VerificationResult:
    """검증 결과를 상세히 담는 데이터 클래스"""
    original_location: LocationInfo
    verified_location: Optional[LocationInfo]
    verification_method: str
    distance_km: Optional[float] = None

class GoogleMapsVerifier:
    """Google Maps API를 사용하여 장소 정보를 검증하는 서비스"""

    def __init__(self):
        if not GOOGLE_MAPS_API_KEY:
            print("❌ GOOGLE_MAPS_API_KEY 환경변수가 설정되지 않았습니다.")
            raise ValueError("GOOGLE_MAPS_API_KEY is not set.")
        self.gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        print("✅ Google Maps Verifier가 성공적으로 초기화되었습니다.")

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """두 좌표 간의 거리를 Haversine 공식을 이용해 킬로미터 단위로 계산합니다."""
        R = 6371  # 지구 반지름 (km)
        lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        a = (math.sin(delta_lat / 2) ** 2) + (math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    async def _search_place_by_name(self, location_name: str, region_context: str | None = None) -> Optional[Dict]:
        """장소 이름을 기반으로 Google Places API를 비동기적으로 검색합니다."""
        loop = asyncio.get_running_loop()
        try:
            search_args = {'query': location_name, 'language': 'ko'}
            
            if region_context:
                print(f"➡️ 지역 컨텍스트 '{region_context}'를 사용하여 검색 범위를 제한합니다.")
                geocode_result = await loop.run_in_executor(None, lambda: self.gmaps.geocode(region_context, language='ko'))
                if geocode_result:
                    loc = geocode_result[0]['geometry']['location']
                    search_args['location'] = (loc['lat'], loc['lng'])
                    search_args['radius'] = 20000  # 20km
                else:
                    print(f"⚠️ 지역 컨텍스트 '{region_context}'의 좌표를 찾을 수 없습니다.")

            places_result = await loop.run_in_executor(
                None, lambda: self.gmaps.places(**search_args)
            )
            
            if places_result and places_result["results"]:
                best_match = places_result["results"][0]
                result = {
                    "place_id": best_match.get("place_id"),
                    "name": best_match.get("name"),
                    "formatted_address": best_match.get("formatted_address"),
                    "lat": best_match["geometry"]["location"]["lat"],
                    "lng": best_match["geometry"]["location"]["lng"],
                    "types": best_match.get("types", []),
                    "rating": best_match.get("rating"),
                }
                return result
            
            print(f"⚠️ Google Maps에서 '{location_name}'에 대한 검색 결과가 없습니다.")
            return None
        except Exception as e:
            print(f"❌ Google Maps API 검색 중 오류 발생 ('{location_name}'): {e}")
            return None

    async def verify_location(self, location: LocationInfo, region_context: str | None = None, distance_threshold_km: float = 2.0) -> VerificationResult:
        """단일 위치 정보를 검증하고, 원본과 검증된 결과를 함께 반환합니다."""
        maps_data = await self._search_place_by_name(location.name, region_context=region_context)

        if not maps_data:
            return VerificationResult(
                original_location=location,
                verified_location=None,
                verification_method="verification_failed",
            )

        verified_loc = LocationInfo(
            name=maps_data["name"],
            lat=maps_data["lat"],
            lng=maps_data["lng"],
            verified=True,
            place_id=maps_data["place_id"],
            formatted_address=maps_data.get("formatted_address"),
            google_rating=maps_data.get("rating"),
            place_types=maps_data.get("types"),
            source="google_maps_verified"
        )

        distance = None
        method = "name_match_coordinates_added" # 기본값: 이름만 일치, 좌표는 새로 추가
        
        if location.lat is not None and location.lng is not None:
            distance = self._calculate_distance(location.lat, location.lng, verified_loc.lat, verified_loc.lng)
            if distance <= distance_threshold_km:
                verified_loc.lat = location.lat
                verified_loc.lng = location.lng
                method = "name_and_coordinates_match"
            else:
                method = "name_match_coordinates_corrected"
        
        return VerificationResult(
            original_location=location,
            verified_location=verified_loc,
            verification_method=method,
            distance_km=distance,
        )

    async def verify_locations_batch(self, locations: List[LocationInfo], region_context: str | None = None) -> List[LocationInfo]:
        """여러 위치 정보를 일괄적으로 검증하고, 검증에 성공한 위치 정보 리스트를 반환합니다."""
        print(f"➡️ {len(locations)}개 위치에 대한 일괄 검증을 시작합니다. (지역: {region_context or 'N/A'})")
        tasks = [self.verify_location(loc, region_context=region_context) for loc in locations]
        verification_results = await asyncio.gather(*tasks)

        verified_locations = []
        for result in verification_results:
            if result.verified_location:
                verified_locations.append(result.verified_location)
            else:
                print(f"⚠️ 검증 실패: '{result.original_location.name}'")
        
        return verified_locations
