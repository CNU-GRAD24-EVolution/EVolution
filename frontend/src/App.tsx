import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import Map from "./components/map-ui/Map";
import Modals from "./components/modals/Modals";
import { ReactComponent as Logo } from "./assets/logo.svg";
import { ReactComponent as IconArrowDown } from "./assets/icons/info/arrow-down.svg";

function App() {
  /** react-query client*/
  const queryClient = new QueryClient();

  /** 실시간 교통 토글 활성화 상태 */
  const [isTrafficActive, setIsTrafficActive] = useState<boolean>(true);

  return (
    <QueryClientProvider client={queryClient}>
      <Modals />
      <div className="m-0 w-full max-w-full p-0">
        <div className="relative mx-auto max-w-[1200px]">
          <div className="flex justify-center gap-[58px] overflow-y-hidden md:px-10">
            <div className="hidden h-dvh w-full max-w-[512px] md:block">
              <h1 className="text-2xl">PC 환경 브랜딩</h1>
            </div>
            <div className="relative h-dvh w-full min-w-[375px] overflow-y-auto bg-white md:max-w-[375px]">
              <div id="modal-root"></div>
              <div id="detailed-info-view-root"></div>
              <main className="flex flex-col h-full">
                {/* 헤더 */}
                <header className="h-[58px] w-full flex items-center gap-2 border-b-[1px] border-solid border-[#F0F0F0] bg-white p-3 font-bold">
                  <Logo width={30} height={30} />
                  EVolution
                </header>
                {/* 검색창, 필터, 토글스위치 */}
                <div className="flex flex-col w-full gap-3 p-3">
                  <form action="" method="get" className="w-full">
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
                  </form>
                  <form
                    action=""
                    method="get"
                    className="w-full overflow-x-scroll"
                  >
                    <div className="flex gap-1">
                      {["충전기 타입", "속도", "충전소 상태", "주차료"].map(
                        (category) => (
                          <button
                            className="rounded-full border border-[#D6DAE1] px-3 py-1 flex flex-shrink-0 items-center justify-center gap-1"
                            key={category}
                          >
                            <span className=" text-black-light text-sm">
                              {category}
                            </span>
                            <IconArrowDown fill="#535353" width={16} />
                          </button>
                        )
                      )}
                    </div>
                  </form>
                  <div className="w-full flex gap-3 items-center">
                    <label className="flex items-center cursor-pointer">
                      <span className="me-2 text-xs text-gray-900 ">
                        1시간 이내 예상혼잡도
                      </span>
                      <input
                        type="checkbox"
                        value=""
                        className="appearance-none relative w-11 h-6 bg-gray-200 focus:outline-none rounded-full  checked:after:translate-x-full rtl:checked:after:-translate-x-full checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all checked:bg-green-400"
                      />
                    </label>
                    <label className="flex items-center cursor-pointer">
                      <span className="me-2 text-xs text-gray-900 ">
                        실시간교통
                      </span>
                      <input
                        name="traffic"
                        type="checkbox"
                        value=""
                        defaultChecked
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                          setIsTrafficActive(e.target.checked);
                        }}
                        className="appearance-none relative w-11 h-6 bg-gray-200 focus:outline-none rounded-full  checked:after:translate-x-full rtl:checked:after:-translate-x-full checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all checked:bg-green-400"
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
