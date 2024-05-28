import { create } from "zustand";

/** 예상혼잡도 버튼 상태 */
interface PredictBtnState {
  /** 활성화 여부 */
  isActivate: boolean;
  /** 활성화 토글 */
  toggleActivation: () => void;
}

export const usePredictBtnState = create<PredictBtnState>()((set) => ({
  isActivate: false,
  toggleActivation: () =>
    set((state) => ({
      isActivate: !state.isActivate,
    })),
}));
