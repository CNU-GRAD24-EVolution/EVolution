import { MapMarker } from "react-kakao-maps-sdk";
import { StationSummarized } from "../../types/station";
import { useViewingStationStore } from "../../store/viewing-station";
import BriefInfoView from "../info-views/BriefInfoView";

/** 지도상의 충전소 마커 */
export default function StationMarker({
  station,
}: {
  station: StationSummarized;
}) {
  /** 유저가 현재 선택한 마커의 충전소 ID */
  const viewingStatId = useViewingStationStore((state) => state.statId);

  /** 현재 선택한 마커의 충전소 ID 설정 */
  const setViewingStatId = useViewingStationStore((state) => state.setStatId);

  /** 마커를 클릭하면 현재 선택한 충전소로 설정 */
  const setAsViewingStation = () => {
    setViewingStatId(station.statId);
  };

  let imageSrc;
  // 충전가능 마커
  if (station.info.usableChargers > 0) {
    imageSrc = require("../../assets/markers/able.svg").default;
  }
  // 사용중 마커
  else if (
    station.info.usableChargers === 0 &&
    station.info.usingChargers > 0
  ) {
    imageSrc = require("../../assets/markers/using.svg").default;
  }
  // 상태미확인 마커
  else if (
    station.info.usableChargers === 0 &&
    station.info.usingChargers === 0
  ) {
    imageSrc = require("../../assets/markers/unknown.svg").default;
  }

  // 마커를 선택한 경우
  if (viewingStatId === station.statId) {
    imageSrc = require("../../assets/markers/selected-no-pred.svg").default;
  }

  return (
    <div className="marker">
      <MapMarker
        image={{
          src: imageSrc,
          size: { width: 30, height: 40 },
        }}
        key={`marker-${station.statId}-${station.info.lat},${station.info.lng}`}
        position={{
          lat: parseFloat(station.info.lat),
          lng: parseFloat(station.info.lng),
        }}
        onClick={setAsViewingStation}
        title="marker"
      ></MapMarker>
      {/* 마커를 선택하면 간략정보를 표시 */}
      {viewingStatId === station.statId && <BriefInfoView station={station} />}
    </div>
  );
}
