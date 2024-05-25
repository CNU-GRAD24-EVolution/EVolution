import { createPortal } from "react-dom";
import { useModalsStore } from "../../store/modals";
import { Fragment } from "react";

/** react portal로 전역에서 관리되는 모달들을 표시해주는 컴포넌트 */
export default function Modals() {
  /** 스토어에 등록된 모든 모달 */
  const modals = useModalsStore((state) => state.modals);

  /** 모달이 표시될 위치 */
  const portalElement = document.getElementById("modal-root") as HTMLElement;

  /** isOpen: true인 모달들을 모두 표시 */
  return portalElement ? (
    createPortal(
      <>
        {modals.map((modal) => {
          return <Fragment key={modal.id}>{modal.content}</Fragment>;
        })}
      </>,
      portalElement
    )
  ) : (
    <></>
  );
}
