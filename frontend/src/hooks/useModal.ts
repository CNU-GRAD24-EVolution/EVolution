import { useCallback, useEffect, useMemo } from "react";
import { useHideModal, useShowModal } from "../store/modals";
import { nanoid } from "nanoid";
import { JSX } from "react";

/** Modals Store에 새로운 모달을 등록하고 해당 모달을 쉽게 여닫을 수 있는 함수를 반환하는 Custom Hook */
export default function useModal(content: JSX.Element) {
  /** 새 modal id 생성 */
  const newId = useMemo(() => nanoid(10), []);

  /** 모달 관련 액션함수들 */
  const showModal = useShowModal();
  const hideModal = useHideModal();

  /** 모달 열기 */
  const show = useCallback(() => {
    showModal({ id: newId, content: content });
  }, [newId]);

  /** 모달 닫기 */
  const hide = useCallback(() => {
    hideModal();
  }, []);

  /** 생성된 모달의 id와 여닫기 함수 반환 */
  return { show, hide };
}
