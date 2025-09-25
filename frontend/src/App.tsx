import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import Map from './components/map-ui/Map';
import Modals from './components/modals/Modals';
import { ReactComponent as Logo } from './assets/logo.svg';
import { usePredictBtnState } from './store/predict-btn';
import Branding from './components/branding/Branding';
import SearchFilter from './components/search-filter/SearchFilter';

function App() {
  /** react-query client */
  const queryClient = new QueryClient();

  /** 실시간 교통 토글 활성화 상태 */
  const [isTrafficActive, setIsTrafficActive] = useState<boolean>(true);

  /** 예상혼잡도 버튼 활성화 토글 함수 */
  const togglePredict = usePredictBtnState((state) => state.toggleActivation);

  return (
    <QueryClientProvider client={queryClient}>
      <Modals />
      <div className="m-0 w-full max-w-full p-0">
        <div className="relative mx-auto max-w-[1200px]">
          <div className="flex justify-center gap-[58px] overflow-y-hidden md:px-10">
            <div className="hidden h-dvh w-full max-w-[512px] md:block">
              <Branding />
            </div>
            <div className="relative h-dvh w-full min-w-[375px] overflow-y-auto bg-white md:max-w-[375px]">
              <div id="modal-root"></div>
              <div id="detailed-info-view-root"></div>
              <main className="flex flex-col h-full">
                {/* 헤더 */}
                <header className="h-[58px] w-full flex items-center gap-1 border-b-[1px] border-solid border-[#F0F0F0] bg-white p-3 font-bold text-lg">
                  <Logo width={26} height={26} />
                  EVolution
                </header>
                {/* 검색창, 필터, 토글스위치 */}
                <div className="flex flex-col w-full gap-3 p-3">
                  {/* <form action="" method="get" className="w-full">
                    <div className="flex items-center bg-[#F8FAFB] border border-[#D6DAE1] rounded-md px-3 py-2 gap-1">
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        className="w-5 h-5 stroke-gray-400 stroke-2"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
                        />
                      </svg>
                      <label htmlFor="name"></label>
                      <input
                        type="text"
                        name="name"
                        id="name"
                        placeholder="관심있는 충전소 이름을 입력해보세요"
                        required
                        className="bg-transparent rounded-md w-full p-0 placeholder:text-gray-400"
                      />
                    </div>
                  </form> */}
                  <SearchFilter />
                  <div className="w-full flex gap-3 items-center">
                    <label className="flex items-center cursor-pointer">
                      <span className="me-2 text-xs font-semibold text-black-light ">1시간 이내 예상혼잡도</span>
                      <input type="checkbox" value="" className="toggle-btn" onClick={togglePredict} />
                    </label>
                    <label className="flex items-center cursor-pointer">
                      <span className="me-2 text-xs font-semibold  text-black-light ">실시간교통</span>
                      <input
                        name="traffic"
                        type="checkbox"
                        value=""
                        defaultChecked
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                          setIsTrafficActive(e.target.checked);
                        }}
                        className="toggle-btn"
                      />
                    </label>
                  </div>
                </div>
                {/* 지도 */}
                <Map traffic={isTrafficActive} />
              </main>
            </div>
          </div>
        </div>
      </div>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
