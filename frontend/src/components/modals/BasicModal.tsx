import { useState } from "react";
import { ReactComponent as IconX } from "../../assets/icons/X.svg";
import { useHideModal } from "../../store/modals";

/** 우상단에 닫기 아이콘이 있는 기본 모달
 * @prop children: 모달에 표시할 내용(JSX)
 */
export default function BasicModal({
  children,
}: {
  children: React.ReactNode;
}) {
  const hide = useHideModal();
  const [open, setOpen] = useState<boolean>(true);

  return (
    /* 모달 오버레이 영역 */
    <div className="absolute w-full inset-0 flex items-center justify-center z-[4] bg-black bg-opacity-50 transition-opacity">
      {/* 모달 컨테이너 영역 */}
      <div
        className={`animate-show relative bg-white flex items-center justify-center z-[3] overflow-y-auto px-[12px] py-[40px] rounded-lg min-h-[200px] min-w-[80%] max-w-[90%] max-h-[70%] overflow-auto`}
      >
        {/* 닫기버튼 */}
        <div
          className="absolute top-[12px] right-[12px] cursor-pointer"
          onClick={() => {
            setOpen(false);
            setTimeout(() => {
              hide();
            }, 200);
          }}
        >
          <IconX width={20} height={20} />
        </div>
        {/* 모달 내용 영역 */}
        {children}
      </div>
    </div>
  );
}
