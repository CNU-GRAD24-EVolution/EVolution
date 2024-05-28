import { MapMarker } from "react-kakao-maps-sdk";
import { StationSummarized } from "../../types/station";
import { useViewingStationStore } from "../../store/viewing-station";
import BriefInfoView from "../info-views/BriefInfoView";
import { usePredictBtnState } from "../../store/predict-btn";
import { predict1HourVisitNum } from "../../utils/utils-charger";

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

  /** 예상혼잡도 버튼 활성화 상태 구독 */
  const isPredictActivate = usePredictBtnState((state) => state.isActivate);

  /** 마커 이미지 속성 */
  let imageAttr;
  let imageSrc;
  let imageSize = { width: 30, height: 40 };

  // 충전가능 마커
  if (station.info.usableChargers > 0) {
    imageSrc = require("../../assets/markers/able.svg").default;
    imageAttr = {
      src: imageSrc,
      size: imageSize,
    };
  }
  // 사용중 마커
  else if (
    station.info.usableChargers === 0 &&
    station.info.usingChargers > 0
  ) {
    imageSrc = require("../../assets/markers/using.svg").default;
    imageAttr = {
      src: imageSrc,
      size: imageSize,
    };
  }
  // 상태미확인 마커
  else if (
    station.info.usableChargers === 0 &&
    station.info.usingChargers === 0
  ) {
    imageSrc = require("../../assets/markers/unknown.svg").default;
    imageAttr = {
      src: imageSrc,
      size: imageSize,
    };
  }

  /** 예상혼잡도 활성화 시 (우선순위 1) */
  // 충전가능한 충전소에 대해 예상혼잡도 표시
  if (
    isPredictActivate &&
    station.info.usableChargers > 0 &&
    station.demandInfo
  ) {
    /** 예상혼잡도 계산 */
    const predictResult = predict1HourVisitNum(station);

    // 예상혼잡도 (예상이용객수 / 전체 충전기대수)
    const busyRate = predictResult / station.info.totalChargers;

    if (busyRate >= 0.75) {
      imageSrc = require("../../assets/markers/predict-crowded.svg").default;
      imageAttr = {
        src: imageSrc,
        size: { width: 30 * 1.2, height: 40 * 1.16 },
      };
    } else {
      imageSrc = require("../../assets/markers/predict-free.svg").default;
      imageAttr = {
        src: imageSrc,
        size: { width: 30 * 1.2, height: 40 * 1.16 },
      };
    }
  }

  // 모두 사용중인 충전소에 대해 예상혼잡도 표시 (일단은 무조건 혼잡예상으로 처리했음)
  if (
    isPredictActivate &&
    station.info.usableChargers === 0 &&
    station.info.usingChargers > 0
  ) {
    imageSrc =
      require("../../assets/markers/predict-using-crowded.svg").default;
    imageAttr = {
      src: imageSrc,
      size: { width: 30 * 1.2, height: 40 * 1.16 },
    };
  }

  // 마커를 선택한 경우 (우선순위 0)
  if (viewingStatId === station.statId) {
    imageSrc = require("../../assets/markers/selected-no-pred.svg").default;
    imageAttr = {
      src: imageSrc,
      size: imageSize,
    };
  }

  return (
    <div className="marker">
      <MapMarker
        image={imageAttr}
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
