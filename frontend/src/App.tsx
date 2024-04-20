import React, { useState } from "react";
import Map from "./components/map-ui/Map";

function App() {
  const [isTrafficActive, setIsTrafficActive] = useState<boolean>(false);

  return (
    <div className="m-0 w-full max-w-full p-0">
      <div className="relative mx-auto max-w-[1200px]">
        <div className="flex justify-center gap-[58px] overflow-y-hidden md:px-10">
          <div className="hidden h-dvh w-full max-w-[512px] md:block">
            <h1 className="text-2xl">PC 환경 브랜딩</h1>
          </div>
          <div className="relative h-dvh w-full min-w-[360px] overflow-y-auto bg-white md:max-w-[375px]">
            <main className="flex flex-col h-full">
              {/* 헤더 */}
              <header className="h-[58px] w-full flex items-center justify-between border-b-[1px] border-solid border-[#F0F0F0] bg-white p-3 font-bold">
                [Logo] EVolution
              </header>
              {/* 검색창, 필터, 토글스위치 */}
              <div className="flex flex-col w-full gap-2 p-3">
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
                <form action="" method="get" className="w-full">
                  <div>(필터 자리)</div>
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
  );
}

export default App;
