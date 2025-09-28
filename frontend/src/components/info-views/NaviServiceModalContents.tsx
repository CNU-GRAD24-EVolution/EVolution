/** 경로안내 버튼을 눌렀을 때 표시되는 모달 */

import apiClient from '../../utils/axios';
import { StringLatLng } from '../../types/map';
import BasicModal from '../modals/BasicModal';

const NaviServiceModalContents = ({ statId, statNm, dest }: { statId: string; statNm: string; dest: StringLatLng }) => {
  const style_a =
    'flex-center w-full h-10 bg-gray-light text-black-light font-semibold text-sm rounded-md cursor-pointer';

  /** 30분내 출발 데이터 추가 요청 */
  const updateDepartsIn30m = async () => {
    try {
      const now = new Date().toISOString();
      const response = await apiClient.post(
        `/api/stations/${statId}/departs`,
        {
          depart_time: now
        },
        { headers: { 'content-type': 'application/json' } }
      );
    } catch (error) {
      console.error('30분내 출발 데이터 추가 오류:', error);
    }
  };

  return (
    <BasicModal>
      <div className="flex flex-col gap-2 w-[80%] items-center">
        <h2 className="text-lg font-semibold">경로 안내</h2>
        <ul className="flex flex-col gap-2 w-[80%] my-[10px]">
          <li>
            <a
              className={`${style_a}`}
              href={`https://map.kakao.com/link/to/${statNm},${dest.lat},${dest.lng}`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={updateDepartsIn30m}
            >
              카카오맵
            </a>
          </li>
          <li className={`${style_a}`}>
            <a
              className={`${style_a}`}
              href={`https://map.naver.com?lng=${dest.lng}&lat=${dest.lat}&title=${statNm}`}
              target="_blank"
              rel="noopener noreferrer"
              onClick={updateDepartsIn30m}
            >
              네이버지도
            </a>
          </li>
        </ul>
      </div>
    </BasicModal>
  );
};

export default NaviServiceModalContents;
