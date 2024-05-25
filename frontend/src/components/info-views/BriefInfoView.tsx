import axios from "axios";
import { useViewingStationStore } from "../../store/viewing-station";
import { StationSummarized } from "../../types/station";
import { useQuery } from "@tanstack/react-query";
import { ReactComponent as IconStation } from "../../assets/icons/info/station.svg";
import { ReactComponent as IconCharger } from "../../assets/icons/info/charger.svg";
import { ReactComponent as IconSpeed } from "../../assets/icons/info/speed.svg";
import { ReactComponent as IconTime } from "../../assets/icons/info/time.svg";
import { memo, useCallback, useEffect, useRef, useState } from "react";
import useModal from "../../hooks/useModal";
import NaviServiceModalContents from "./NaviServiceModalContents";
import DetailedInfoView from "./DetailedInfoView";
import { ChargerTypes } from "../../types/charger-types";

/** 충전소 간략정보 화면 */
const BriefInfoView = memo(function ({
  station,
}: {
  station: StationSummarized;
}) {
  /** 정보를 보여줄 충전소 ID */
  const statId = useViewingStationStore((state) => state.statId);

  const setStatId = useViewingStationStore((state) => state.setStatId);

  /** 충전소 간략정보 가져오기 (axios) */
  const getInfo = async <T = StationSummarized,>(): Promise<T> => {
    const { data } = await axios.get<T>(`/api/stations/${statId}`);
    return data;
  };

  // 서버 상태 관리 - 충전소 간략정보 (react-query)
  const { data } = useQuery<StationSummarized>({
    queryKey: ["brief-info", statId],
    queryFn: getInfo,
    enabled: statId !== "",
    staleTime: 30000, // 30초동안 캐시
  });

  /** 간략정보 영역 */
  const infoArea = useRef<HTMLDivElement>(null);

  /** 경로안내 모달 열기 */
  const { show: showModal } = useModal(
    <NaviServiceModalContents
      statId={station.statId}
      statNm={station.info.statNm}
      dest={{ lat: station.info.lat, lng: station.info.lng }}
    />
  );

  /** 경로안내 버튼 클릭 핸들러 */
  const naviBtnHandler = useCallback(() => {
    showModal();
  }, []);

  useEffect(() => {
    /** 지도 영역 */
    const mapArea = document.getElementById("map-area");

    if (mapArea) {
      /** 드래그 여부 감지 */
      let isDrag: boolean;
      mapArea.addEventListener("mousedown", () => {
        isDrag = false;
      });
      mapArea.addEventListener("mousemove", () => {
        isDrag = true;
      });

      /** 마커와 버튼을 제외한 지도 내 영역 클릭 감지 시 간략정보 창 닫기 (드래그가 아닌 경우에만 실행)
       **/
      const handleClick = (e: MouseEvent) => {
        const target = e.target as HTMLElement;
        if (
          !isDrag &&
          infoArea &&
          target !== infoArea.current &&
          target.title !== "marker" &&
          !target.closest("button")?.className.includes("btn-on-map") &&
          target.closest("article")?.id !== "brief-info"
        ) {
          setStatId("");
        }
      };

      /** 지도 영역에 이벤트핸들러 추가 */
      mapArea.addEventListener("mouseup", handleClick);

      /** CleanUp (지도 영역 이벤트핸들러 제거) */
      return () => {
        mapArea.removeEventListener("mouseup", handleClick);
      };
    }
  }, []);

  const info_status = data
    ? data.info.usableChargers > 0
      ? `충전가능 (${data.info.usableChargers}/${data.info.totalChargers})`
      : data!.info.usableChargers === 0 && data!.info.usingChargers > 0
      ? `충전중 (${data.info.usableChargers}/${data.info.totalChargers})`
      : "상태미확인"
    : undefined;

  const info_chargerTypes = data
    ? data.info.chargerTypes
        .map((type: string) => {
          return ChargerTypes[type as keyof typeof ChargerTypes];
        })
        .join(", ")
    : undefined;

  const info_maxOutput = data ? data.info.maxOutput + "kW" : undefined;
  const info_useTime = data ? data.info.useTime || "상태미확인" : undefined;

  /** 상세정보 창 open 상태 */
  const [isDetailedInfoViewOpen, setIsDetailedInfoViewOpen] =
    useState<boolean>(false);

  const toggleIsDetailedInfoView = () =>
    setIsDetailedInfoViewOpen(!isDetailedInfoViewOpen);

  return data ? (
    <>
      <article
        id="brief-info"
        className="absolute bottom-0 left-0 flex w-full bg-white z-[2] p-4 gap-3"
        ref={infoArea}
      >
        {/* 충전소 정보 wrapper*/}
        <div className="flex-1 flex flex-col justify-between gap-2">
          {/* 충전소명 */}
          <h1 className="font-extrabold text-lg leading-6 mb-1">
            {data.info.statNm}
          </h1>
          {/* 충전소 상태 (이용가능/전체대수) */}
          <div className="info-with-icon">
            <IconStation />
            <span
              className={
                info_status!.includes("충전가능")
                  ? "text-green-600"
                  : info_status!.includes("충전중")
                  ? "text-red-600"
                  : ""
              }
            >
              {info_status}
            </span>
          </div>
          {/* 제공 충전기타입 */}
          <div className="info-with-icon">
            <IconCharger />
            <span>{info_chargerTypes}</span>
          </div>
          {/* 최대속도 */}
          <div className="info-with-icon">
            <IconSpeed />
            <span>{info_maxOutput}</span>
          </div>
          {/* 운영시간 */}
          <div className="info-with-icon">
            <IconTime />
            <span>{info_useTime}</span>
          </div>
        </div>
        {/* 버튼 wrapper */}
        <div className="w-1/3 flex flex-col justify-center gap-2">
          {/* 경로안내 버튼 */}
          <button
            className="info-brief-btn bg-black text-white"
            onClick={naviBtnHandler}
          >
            경로안내
          </button>
          {/* 상세정보 버튼 */}
          <button
            className="info-brief-btn bg-[#ECECEC] text-[#535353]"
            onClick={toggleIsDetailedInfoView}
          >
            상세정보
          </button>
        </div>
      </article>
      {isDetailedInfoViewOpen && (
        <DetailedInfoView
          station={station}
          toggleView={toggleIsDetailedInfoView}
        />
      )}
    </>
  ) : (
    <></>
  );
});

export default BriefInfoView;
