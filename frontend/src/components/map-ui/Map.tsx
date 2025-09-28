import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { MarkerClusterer, Map as KakaoMap, MapMarker, MapTypeId } from 'react-kakao-maps-sdk';
import { LatLng } from '../../types/map';
import { debounce } from 'lodash';
import { ReactComponent as IconRefresh } from '../../assets/icons/refresh.svg';
import { ReactComponent as IconMyLocation } from '../../assets/icons/my-location.svg';
import { ReactComponent as IconRecommend } from '../../assets/icons/recommend.svg';
import { ReactComponent as IconMarkerInfo } from '../../assets/icons/marker-info.svg';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import useSearchQueryStore from '../../store/search-query';
import { StationList } from '../../types/station-list';
import StationMarker from './StationMarker';
import useModal from '../../hooks/useModal';
import MarkerInfoModalContents from './MarkerInfoModalContents';

export default function Map({ traffic }: { traffic: boolean }) {
  /** 검색 쿼리 상태 (Zustand) */
  const searchQuery = useSearchQueryStore((state) => state.query); // 검색 쿼리

  /** 쿼리 지도영역필드 업데이트 함수 */
  const setMapRange = useSearchQueryStore((state) => state.setMapRange);

  /** 쿼리스트링 생성하여 얻는 함수 */
  const getSearchQueryString = useSearchQueryStore((state) => state.getQueryString);

  /** 주변 충전소 검색 (axios) */
  const getStationList = async <T = StationList,>(): Promise<T> => {
    const { data } = await axios.get<T>(getSearchQueryString(), {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json' // 요청 데이터 형식
      }
    });
    return data;
  };

  // 서버 상태 관리 - 주변 충전소 검색 (react-query)
  const queryClient = useQueryClient();

  /** 서버에서 받아온 주변 충전소 목록 */
  const { data: stationList } = useQuery<StationList>({
    queryKey: ['stations-nearby', searchQuery],
    queryFn: getStationList
  });

  const mapRef = useRef<kakao.maps.Map>(null);

  // 지도의 중심좌표
  const [center, setCenter] = useState<LatLng>({
    lat: 33.450701,
    lng: 126.570667
  });

  // 현재 위치
  const [position, setPosition] = useState<LatLng>({
    lat: 33.450701,
    lng: 126.570667
  });

  /** 지도의 중심을 유저의 현재 위치로 변경 */
  const setCenterToMyPosition = () => {
    if (!mapRef.current) return;
    mapRef.current.panTo(new kakao.maps.LatLng(position.lat, position.lng));
  };

  // 지도가 처음 렌더링되면 중심좌표를 현위치로 설정하고 위치 변화 감지
  useEffect(() => {
    navigator.geolocation.getCurrentPosition((pos) => {
      setCenter({ lat: pos.coords.latitude, lng: pos.coords.longitude });
    });

    navigator.geolocation.watchPosition((pos) => {
      setPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude });
    });
  }, []);

  /** 마커 안내 모달 열기 */
  const { show: showModal } = useModal(<MarkerInfoModalContents />);
  /** 마커 안내 버튼 클릭 핸들러 */
  const markerInfoButtonHandler = useCallback(() => {
    showModal();
  }, []);

  return (
    <div className="relative w-full h-full" id="map-area">
      {/* 지도 */}
      <KakaoMap // 지도를 표시할 Container
        className="w-full h-full"
        id="map"
        center={center}
        level={4} // 지도의 확대 레벨
        ref={mapRef}
      >
        <MarkerClusterer
          averageCenter={true} // 클러스터에 포함된 마커들의 평균 위치를 클러스터 마커 위치로 설정
          minLevel={6} // 클러스터 할 최소 지도 레벨
        >
          {/* 현위치 마커 */}
          <MapMarker
            image={{
              src: require('../../assets/markers/position.svg').default,
              size: { width: 30, height: 30 }
            }}
            position={position}
          />
          {/* 현위치 주변 충전소들 마커 */}
          {stationList &&
            stationList.map((station) => {
              return <StationMarker key={station.statId} station={station} />;
            })}
        </MarkerClusterer>
        {/* 교통상황 표시 */}
        {traffic && <MapTypeId type={'TRAFFIC'} />}
      </KakaoMap>

      {/* 지도 위 버튼들 */}
      <div className="flex flex-col gap-[10px] absolute z-[1] top-0 right-0 p-[10px]">
        {/* 새로고침 버튼 */}
        <button
          className="btn-on-map"
          onClick={() => {
            queryClient.invalidateQueries({
              queryKey: ['stations-nearby']
            });
          }}
        >
          <IconRefresh width={20} height={20} />
        </button>
        {/* 현위치 버튼 */}
        <button className="btn-on-map" onClick={setCenterToMyPosition}>
          <IconMyLocation width={25} height={25} />
        </button>
        {/* 마커 설명 버튼 */}
        <button className="btn-on-map" onClick={markerInfoButtonHandler}>
          <IconMarkerInfo width={25} height={25} />
        </button>
      </div>
      {/* 추천받기 버튼 */}
      <button className="transition ease-in-out flex gap-2 w-auto py-3 px-4 absolute z-[1] bottom-[30px] right-[10px] justify-center items-center cursor-pointer rounded-full bg-gradient-to-r from-indigo-500 from-10% via-sky-500 via-50% to-emerald-500 to-90% shadow-[0_0_20px_#00000050] hover:-translate-y-2">
        <IconRecommend width={20} height={20} />
        <span className="text-white font-semibold text-base ">추천받기</span>
      </button>
    </div>
  );
}
