import { memo, useCallback, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { StationDetailed, StationSummarized } from '../../types/station';
import NaviServiceModalContents from './NaviServiceModalContents';
import useModal from '../../hooks/useModal';
import apiClient from '../../utils/axios';
import { useQuery } from '@tanstack/react-query';
import { ReactComponent as IconEye } from '../../assets/icons/info/eye.svg';
import { ReactComponent as IconPrev30 } from '../../assets/icons/info/prev30.svg';
import { ReactComponent as IconTime } from '../../assets/icons/info/time.svg';
import { ReactComponent as IconParking } from '../../assets/icons/info/parking.svg';
import { ReactComponent as IconLocation } from '../../assets/icons/info/location.svg';
import { ReactComponent as IconRestrict } from '../../assets/icons/info/restrict.svg';
import { ReactComponent as IconCall } from '../../assets/icons/info/call.svg';
import { ReactComponent as IconArrowDown } from '../../assets/icons/info/arrow-down.svg';
import { ReactComponent as IconPredict } from '../../assets/icons/info/predict.svg';
import { ChargerTypes } from '../../types/charger-types';
import { ChargerStatus } from '../../types/charger-status';
import { calcElaspedTime, yyyyMMddHHmmssToDateTime } from '../../utils/utils-datetime';
import { calcChargeFinishTime, predict1HourVisitNum } from '../../utils/utils-charger';
import VisitNumGraph from './VisitNumGraph';

const DetailedInfoView = memo(({ station, toggleView }: { station: StationSummarized; toggleView: () => void }) => {
  /** 충전소 상세정보 가져오기 (apiClient) */
  const getInfo = async <T = StationDetailed,>(): Promise<T> => {
    const { data } = await apiClient.get<T>(`/api/stations/${station.statId}?brief=no`);
    return data;
  };

  // 서버 상태 관리 - 충전소 상세정보 (react-query)
  const { data } = useQuery<StationDetailed>({
    queryKey: ['detailed-info', station.statId],
    queryFn: getInfo,
    enabled: station.statId !== '',
    refetchInterval: 30000 // 30초마다 가져오기
  });

  /** 포탈 영역 */
  const portalElement = document.getElementById('detailed-info-view-root') as HTMLElement;

  /** 경로안내 모달 열기 */
  const { show: showModal } = useModal(
    <NaviServiceModalContents
      statId={station.statId}
      statNm={station.info.statNm}
      dest={{ lat: station.info.lat, lng: station.info.lng }}
    />
  );

  /** 상세정보 닫기 버튼 클릭 핸들러 */
  const closeBtnHandler = useCallback(async () => {
    // 숨기기 애니메이션 적용 (0.1초 소요)
    setAppear(false);
    // 0.1초가 지나면 화면에서 제거
    setTimeout(() => {
      toggleView();
    }, 100);
  }, []);

  useEffect(() => {
    const decreaseViewNum = async () => {
      try {
        const response = await apiClient.put(`/api/stations/${station.statId}/view-num/down`);
      } catch (error) {
        console.error('조회수 감소 오류:', error);
      }
    };

    // 브라우저나 탭이 닫힐 때 조회수 -1
    window.addEventListener('beforeunload', decreaseViewNum);

    // Clean Up
    return () => {
      // 컴포넌트가 언마운트될 때 조회수 -1
      decreaseViewNum();
      window.removeEventListener('beforeunload', decreaseViewNum);
    };
  }, [station.statId]);

  /** 예상혼잡도 계산 */
  let predictResult;
  // 예상혼잡도 (예상이용객수 / 전체 충전기대수)
  let busyRate;
  let isBusyAsText;
  let altText;

  // 충전가능
  if (station.info.usableChargers > 0) {
    if (station.demandInfo) {
      predictResult = predict1HourVisitNum(station);
      busyRate = predictResult / station.info.totalChargers;
      isBusyAsText = busyRate >= 0.75 ? '혼잡' : '여유';
    }
  } else if (
    // 사용중
    station.info.usableChargers === 0 &&
    station.info.usingChargers > 0
  ) {
    isBusyAsText = '혼잡';
    altText = '모든 충전기가 사용중이에요';
  } else if (
    // 상태미확인
    station.info.usableChargers === 0 &&
    station.info.usingChargers === 0
  ) {
    isBusyAsText = '예측불가';
    altText = '충전기 상태가 확인되지 않아요';
  }

  /**
   * if appear
   * true: 아래에서 올라오며 나타나는 애니메이션 적용
   * false: 아래로 내려가며 사라지는 애니메이션 적용
   */
  const [appear, setAppear] = useState<boolean>(true);

  return portalElement && data ? (
    createPortal(
      <article
        className={`animate-appearFromBottom ${
          !appear ? 'animate-hideFromTop' : ''
        } absolute left-0 w-full h-full bg-[#F3F5F8] z-[3] overflow-y-auto`}
      >
        {/* 헤더 */}
        <div className="sticky top-0 w-full h-auto bg-white p-3 text-center font-semibold border-b-[1px] border-[#F3F5F8]">
          <div
            className="flex-center absolute top-[50%] -translate-y-[50%] left-[16px] cursor-pointer w-[30px] h-[30px]"
            onClick={closeBtnHandler}
          >
            <IconArrowDown fill="black" />
          </div>
          {data.info.statNm}
        </div>
        {/* 상세정보 컨텐츠 */}
        <div className="w-full h-auto flex flex-col gap-4 p-4 mb-[100px]">
          {/* 충전소명, 주소, 조회수, 출발자수 */}
          <div className="detail-info-section ">
            <div>
              <h1>{data.info.statNm}</h1>
              <h2 className="text-[#A8A8A8] font-semibold text-sm">{data.info.addr}</h2>
            </div>
            <div className="flex flex-col gap-2">
              <div className="info-with-icon">
                <IconEye />
                <span>
                  현재 <strong>{data.demandInfo?.viewNum || 0}명</strong>이 조회중이에요
                </span>
              </div>
              <div className="info-with-icon">
                <IconPrev30 />
                <span>
                  지난 30분 동안 <strong>{data.demandInfo?.departsIn30m.length || 0}명</strong>이 출발했어요
                </span>
              </div>
            </div>
          </div>
          {/* 1시간내 예상혼잡도 */}
          {station.demandInfo && (
            <div className="detail-info-section ">
              <div>
                <h1>예상 혼잡여부</h1>
                <h2 className="text-[#A8A8A8] font-semibold text-xs">앞으로 1시간동안 충전소가 혼잡할지 알려드려요</h2>
              </div>
              <div className="flex flex-col gap-1">
                {/* 혼잡 or 여유 or 예측불가 */}
                {isBusyAsText && <span className="font-extrabold text-2xl">{isBusyAsText}</span>}
                {/* 예상이용객수 */}
                {predictResult !== undefined && (
                  <div className="info-with-icon">
                    <IconPredict />
                    <span>
                      1시간 내로 <strong>{predict1HourVisitNum(station)}명</strong>이 사용할 것으로 예상돼요
                    </span>
                  </div>
                )}
                {/* 설명 */}
                {altText && <span className="text-[#A8A8A8] font-semibold text-sm">{altText}</span>}
              </div>
            </div>
          )}
          {/* 충전기 상태 */}
          <div className="detail-info-section">
            <h1>충전기 상태</h1>
            <div className="flex flex-col gap-3">
              {Array.from(new Set(data.chargers.map((chgr) => chgr.output))).map((output) => {
                if (!output || output.length === 0)
                  return (
                    <div className="text-sm text-[#A1A1A1]" key={output}>
                      충전기 상태 미제공
                    </div>
                  );
                return (
                  <div key={output}>
                    {/* 충전기 속도 */}
                    <h2 className="font-medium">{output}kW</h2>
                    {/* 충전기 타입 */}
                    <div className="text-xs text-[#A1A1A1] font-light">
                      {
                        ChargerTypes[
                          data.chargers.filter((chgr) => chgr.output === output)[0]
                            .chgerType as keyof typeof ChargerTypes
                        ]
                      }
                    </div>
                    {/* 충전기 상태*/}
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      {data.chargers
                        .filter((chgr) => chgr.output === output)
                        .map((chgr) => {
                          /** 마지막 충전시작시간이 16시간 이내인지 여부
                           * 16시간 이상인 경우 갱신 안된것으로 판단
                           */
                          const isLastTsdtFresh =
                            chgr.stat === '3' &&
                            !!chgr.lastTsdt?.trim() &&
                            Date.now() - yyyyMMddHHmmssToDateTime(chgr.lastTsdt) < 16 * 60 * 60 * 1000;

                          return (
                            <div className="flex flex-col bg-[#F4F4F4] rounded-md p-2" key={chgr.chgerId}>
                              {/* 상태 */}
                              <span
                                className={`text-sm font-semibold ${
                                  chgr.stat === '2'
                                    ? 'text-emerald-500'
                                    : chgr.stat === '3'
                                      ? 'text-black-light'
                                      : 'text-[#A1A1A1]'
                                }`}
                              >
                                {ChargerStatus[('0' + chgr.stat) as keyof typeof ChargerStatus]}
                              </span>
                              {/* 마지막 충전종료 시각 */}
                              {chgr.stat !== '3' && (
                                <span className="text-xs font-normal text-[#A1A1A1]">
                                  {!!chgr.lastTedt?.trim()
                                    ? `${calcElaspedTime(yyyyMMddHHmmssToDateTime(chgr.lastTedt))} 전 종료`
                                    : '마지막 충전시각 미확인'}
                                </span>
                              )}
                              {/* 충전시작 시각 (충전중일 시) */}
                              {chgr.stat === '3' && (
                                <span className="text-xs font-normal text-[#A1A1A1]">
                                  {isLastTsdtFresh
                                    ? `${calcElaspedTime(yyyyMMddHHmmssToDateTime(chgr.lastTsdt!))} 경과`
                                    : '시작시간 미확인'}
                                </span>
                              )}
                              {/* 예상 대기시간 (충전중이고 시작시간 제공 시) */}
                              {chgr.stat === '3' && isLastTsdtFresh && (
                                <span className="text-xs font-normal text-[#A1A1A1]">
                                  <strong className="text-red-400">예상대기시간</strong>{' '}
                                  {calcElaspedTime(
                                    calcChargeFinishTime(yyyyMMddHHmmssToDateTime(chgr.lastTsdt!), Number(output))
                                  )}
                                </span>
                              )}
                            </div>
                          );
                        })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          {/* 기본 정보 */}
          <div className="detail-info-section ">
            <div>
              <h1>기본 정보</h1>
            </div>
            <div className="flex flex-col gap-2">
              <div className="info-with-icon">
                <IconTime />
                <span>{data.info.useTime || '운영시간 미제공'}</span>
              </div>
              <div className="info-with-icon">
                <IconParking />
                <span>{data.info.parkingFree === 'Y' ? '무료주차' : '유료주차'}</span>
              </div>
              <div className="info-with-icon">
                <IconLocation />
                <span>
                  {data.info.location !== 'null' && data.info.location !== null
                    ? data.info.location
                    : '상세위치 미제공'}
                </span>
              </div>
              <div className="info-with-icon">
                <IconRestrict />
                <span>{data.info.limitDetail || '이용제한 없음'}</span>
              </div>
              <div className="info-with-icon">
                <IconCall />
                <span>
                  {data.info.busiCall !== 'null' ? (
                    <a href={`tel: ${data.info.busiCall}`} className="text-blue-500">
                      {data.info.busiCall}
                    </a>
                  ) : (
                    '문의 전화번호 미제공'
                  )}
                </span>
              </div>
            </div>
          </div>
          {/* 이용객수 예상 그래프 */}
          {data.demandInfo && data.demandInfo.hourlyVisitNum.length > 0 && (
            <div className="detail-info-section">
              <div>
                <h1>이용객수 예상 그래프</h1>
                <h2 className="text-[#A8A8A8] font-semibold text-xs">
                  지난 30일동안의 충전이력을 기반으로 예측한 금일 이용객수 그래프예요
                </h2>
                <VisitNumGraph data={data.demandInfo.hourlyVisitNum} />
              </div>
            </div>
          )}
        </div>

        {/* 경로안내 버튼 */}
        <div className="fixed bottom-0 w-full h-auto p-4 bg-slate-100 md:max-w-[375px]">
          <button className="w-full h-auto info-brief-btn bg-black text-white p-4 cursor-pointer" onClick={showModal}>
            경로안내
          </button>
        </div>
      </article>,
      portalElement
    )
  ) : (
    <></>
  );
});

export default DetailedInfoView;
