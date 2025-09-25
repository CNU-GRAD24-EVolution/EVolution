import { StationDetailed, StationSummarized } from "../types/station";

/** 80% 충전되기까지 예상되는 시각 (밀리초) */
export const calcChargeFinishTime = (startTime: number, output: number) => {
  const minTake = Math.floor((70 / (output * 0.8)) * 60 * 0.8);
  /* 충전시작시각이 16시간 전인 경우 갱신이 되지 않은 것으로 판단하고 대기시간을 0분으로 처리 */
  if (Math.abs(startTime - Date.now()) > 16 * 60 * 60 * 1000) return Date.now();
  return startTime + minTake * 60 * 1000;
};

/** 1시간내 예상이용객수 계산  */
export const predict1HourVisitNum = (
  station: StationSummarized | StationDetailed
) => {
  // 현재 시
  const hourNow = new Date().getHours();
  // 현재 조회수
  const paramA = station.demandInfo!.viewNum;
  // 30분내 출발자수
  const paramB = station.demandInfo!.departsIn30m.length;
  // 30일간 충전이력 기반 예상 방문자수
  const vnArr = station.demandInfo!.hourlyVisitNum;
  const paramC =
    (vnArr.length === 24 &&
      Math.round(
        ((hourNow === 0 ? 0 : vnArr[hourNow - 1]) + vnArr[hourNow]) / 2
      )) ||
    0;
  // 현재 이용중인 충전기 대수
  const usingNum = station.info.usingChargers;

  // 최종 1시간내 예상이용객수
  const predictResult = Math.round(
    usingNum * 0.8 + paramB * 0.8 + paramA * 0.33 + paramC * 0.5
  );

  return predictResult;
};
