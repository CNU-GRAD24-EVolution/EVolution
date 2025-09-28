/** 마커 안내 버튼을 눌렀을 때 표시되는 모달 */

import BasicModal from '../modals/BasicModal';
import { ReactComponent as MarkerInfoImage } from '../../assets/markerInfo.svg';

const MarkerInfoModalContents = () => {
  return (
    <BasicModal>
      <div className="flex flex-col gap-2 w-[80%] items-center">
        <h2 className="text-lg font-semibold">마커 안내</h2>
        <MarkerInfoImage width={200} height={150} />
      </div>
    </BasicModal>
  );
};

export default MarkerInfoModalContents;
