import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { devtools } from 'zustand/middleware';
import SearchQuery, { MapRange } from '../types/search-query';

/** 검색 쿼리 State **/
interface SearchQueryState {
  query: SearchQuery;
  setMapRange: (range: MapRange) => void;
  setFilter: (categoryType: string, value: string[]) => void;
  getQueryString: () => string;
}

/** 검색 쿼리 State를 관리하는 Store */
const useSearchQueryStore = create<SearchQueryState>()(
  devtools(
    immer((set, get) => ({
      query: {
        /** 지도 영역 */
        mapRange: undefined,
        /** (추가예정) 필터 값들 */
        filter: {
          chargerTypes: [],
          minOutput: [],
          parkingFree: []
        }
      },

      /** 지도 영역을 업데이트하는 함수 */
      setMapRange: (range) =>
        set((state) => {
          state.query.mapRange = range;
        }),

      /** 필터 값 업데이트하는 함수 */
      setFilter: (categoryType: string, value: string[]) =>
        set((state) => {
          state.query.filter[categoryType] = value;
        }),

      /** 쿼리 상태에 기반하여 URI 쿼리스트링을 만드는 함수 */
      getQueryString: () => {
        const baseUrl = process.env.REACT_APP_API_URL || '';
        let queryStr = `${baseUrl}/api/stations?`;
        const query = get().query;
        if (query.mapRange) {
          const { minLat, maxLat, minLng, maxLng } = query.mapRange;
          queryStr += `minLat=${minLat}&maxLat=${maxLat}&minLng=${minLng}&maxLng=${maxLng}`;
        }

        let filterQueries = [];
        if (query.filter.chargerTypes.length > 0) {
          filterQueries.push(`chargerTypes=${query.filter.chargerTypes.join(',')}`);
        }
        if (query.filter.minOutput.length > 0) {
          filterQueries.push(`minOutput=${query.filter.minOutput.join(',')}`);
        }
        if (query.filter.parkingFree.length > 0) {
          filterQueries.push(`parkingFree=${query.filter.parkingFree.join(',')}`);
        }

        queryStr += filterQueries.join('&');
        console.log(queryStr);

        return queryStr;
      }
    }))
  )
);

export default useSearchQueryStore;
