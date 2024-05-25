// 검색 쿼리 관련 인터페이스들

// 지도 영역
export type MapRange =
  | {
      minLat: number;
      maxLat: number;
      minLng: number;
      maxLng: number;
    }
  | undefined;

// 검색 쿼리
export default interface SearchQuery {
  mapRange: MapRange;
}
