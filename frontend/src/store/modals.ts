import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { JSX } from "react";

interface SingleModal {
  id: string;
  content: JSX.Element;
}

/** 모든 모달들의 상태, 모달 여닫기 및 등록 함수를 갖는 State */
interface ModalsState {
  modals: SingleModal[];
  hideModal: () => void;
  showModal: (modal: SingleModal) => void;
}

/** 모달들의 상태를 관리하는 Store */
export const useModalsStore = create<ModalsState>()(
  immer((set) => ({
    /** 각 모달의 상태 (id, isOpen) */
    modals: [],

    /** 최상단의 모달을 닫기 */
    hideModal: () =>
      set((state) => {
        state.modals.pop();
      }),

    /** 새로운 모달을 modals에 등록 */
    showModal: (modal: SingleModal) =>
      set((state) => {
        state.modals.push(modal);
      }),
  }))
);

/** 액션함수들을 쉽게 쓰기위한 custom hook */
export const useShowModal = () => useModalsStore((state) => state.showModal);
export const useHideModal = () => useModalsStore((state) => state.hideModal);
