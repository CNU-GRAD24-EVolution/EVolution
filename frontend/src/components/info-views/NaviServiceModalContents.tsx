/** 경로안내 버튼을 눌렀을 때 표시되는 모달 */

import axios, { AxiosError } from "axios";
import { LatLng, StringLatLng } from "../../types/map";
import BasicModal from "../modals/BasicModal";

const NaviServiceModalContents = ({
  statId,
  statNm,
  dest,
}: {
  statId: string;
  statNm: string;
  dest: StringLatLng;
}) => {
  const style_a =
    "flex-center w-full h-10 bg-gray-light text-black-light font-semibold text-sm rounded-md cursor-pointer";

  /** 30분내 출발 데이터 추가 요청 */
  const updateDepartsIn30m = async () => {
    try {
      const response = axios.post("/api/stations/:{statId}/departs");
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        // axios에서 발생한 error
        const { code } = error.response.data;
      }
    }
  };

  return (
    <BasicModal>
      <ul className="flex flex-col gap-2 w-[80%]">
        <li>
          <a
            className={`${style_a}`}
            href={`https://map.kakao.com/link/to/${statNm},${dest.lat},${dest.lng}`}
            target="_blank"
            rel="noopener noreferrer"
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
          >
            네이버지도
          </a>
        </li>
      </ul>
    </BasicModal>
  );
};

export default NaviServiceModalContents;
