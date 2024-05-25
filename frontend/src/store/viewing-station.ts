import { create } from "zustand";
import { devtools } from "zustand/middleware";

/** 유저가 선택한 마커의 충전소 State */
interface ViewingStationState {
  /** @type {string} 유저가 선택한 마커의 충전소 ID */
  statId: string;
  /**
   * 유저가 선택한 마커의 충전소 ID 설정
   * @param {string} id 충전소 ID
   * @returns {void}
   */
  setStatId: (id: string) => void; //
}

/** 유저가 선택한 마커의 충전소 State를 관리하는 Store */
export const useViewingStationStore = create<ViewingStationState>()(
  devtools((set) => ({
    statId: "",
    setStatId: (id: string) =>
      set({
        statId: id,
      }),
  }))
);
