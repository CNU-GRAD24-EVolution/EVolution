import { useEffect, useMemo, useState } from "react";
import { Map as KakaoMap, MapMarker, MapTypeId } from "react-kakao-maps-sdk";
import { LatLng } from "../../types/map";
import { debounce } from "lodash";
import { ReactComponent as IconRefresh } from "../../assets/icons/refresh.svg";
import { ReactComponent as IconMyLocation } from "../../assets/icons/my-location.svg";
import { ReactComponent as IconRecommend } from "../../assets/icons/recommend.svg";

export default function Map({ traffic }: { traffic: boolean }) {
  // 지도의 중심좌표
  const [center, setCenter] = useState<LatLng>({
    lat: 33.450701,
    lng: 126.570667,
  });

  // 현재 위치
  const [position, setPosition] = useState<LatLng>({
    lat: 33.450701,
    lng: 126.570667,
  });

  // 지도의 중심을 유저의 현재 위치로 변경
  const setCenterToMyPosition = () => {
    setCenter(position);
  };

  // 지도 중심좌표 이동 감지 시 이동된 중심좌표로 설정
  const updateCenterWhenMapMoved = useMemo(
    () =>
      debounce((map: kakao.maps.Map) => {
        setCenter({
          lat: map.getCenter().getLat(),
          lng: map.getCenter().getLng(),
        });
      }, 500),
    []
  );

  // 지도가 처음 렌더링되면 중심좌표를 현위치로 설정하고 위치 변화 감지
  useEffect(() => {
    navigator.geolocation.getCurrentPosition((pos) => {
      setCenter({ lat: pos.coords.latitude, lng: pos.coords.longitude });
    });

    navigator.geolocation.watchPosition((pos) => {
      setPosition({ lat: pos.coords.latitude, lng: pos.coords.longitude });
    });
  }, []);

  return (
    <div className="relative w-full h-full">
      {/* 지도 */}
      <KakaoMap // 지도를 표시할 Container
        className="w-full h-full"
        id="map"
        center={center}
        level={4} // 지도의 확대 레벨
        onCenterChanged={updateCenterWhenMapMoved}
      >
        {/* 현위치 마커 */}
        <MapMarker
          image={{
            src: require("../../assets/markers/position.svg").default,
            size: { width: 30, height: 30 },
          }}
          position={position}
        />
        {/* 교통상황 표시 */}
        {traffic && <MapTypeId type={"TRAFFIC"} />}
      </KakaoMap>

      {/* 지도 위 버튼들 */}
      <div className="flex flex-col gap-[10px] absolute z-[1] top-0 right-0 p-[10px]">
        {/* 새로고침 버튼 */}
        <button className="flex justify-center items-center cursor-pointer rounded-full w-[45px] h-[45px] bg-white shadow-[0_0_8px_#00000025]">
          <IconRefresh width={20} height={20} />
        </button>
        {/* 현위치 버튼 */}
        <button
          className="flex justify-center items-center cursor-pointer rounded-full w-[45px] h-[45px] bg-white shadow-[0_0_8px_#00000025]"
          onClick={setCenterToMyPosition}
        >
          <IconMyLocation width={25} height={25} />
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
