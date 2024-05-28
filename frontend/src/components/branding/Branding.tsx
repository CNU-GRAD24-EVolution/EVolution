import { ReactComponent as IconLogo } from "../../assets/logo.svg";
import { ReactComponent as SVGCoupleUsingCharger } from "../../assets/branding/couple-using-evcharger.svg";
import { ReactComponent as IconNews } from "../../assets/branding/news.svg";
import { ReactComponent as IconFeedback } from "../../assets/branding/feedback.svg";
import { ReactComponent as IconShare } from "../../assets/branding/share.svg";

const Branding = () => {
  return (
    <div className="w-full h-full flex items-center">
      <div className="w-full flex flex-col">
        {/* 로고 */}
        <div className="mb-4 flex-center bg-white rounded-[18px] w-[64px] h-[64px] p-2 shadow-[0_4px_24px_0px_rgba(0,0,0,0.06),0_4px_5px_0px_rgba(0,0,0,0.04)]">
          <IconLogo />
        </div>
        {/* 서비스명 */}
        <h1 className="mb-2 text-[48px] font-extrabold text-[#164a9d]">
          EV
          <span className="font-extrabold text-[#191F28]">olution</span>
        </h1>
        {/* 서비스설명 */}
        <h2 className="mb-[56px] text-[16px] font-medium text-[#343E4B]">
          내 주변의 수많은 전기차 충전소들 중 어디에 가면 좋을지,<br></br>앞으로
          1시간 동안 이용객이 몰리지는 않을지 알려드릴게요!
        </h2>
        {/* 뉴스피드 */}
        <div
          className="relative mb-6 flex flex-col rounded-2xl p-8"
          style={{
            background:
              "linear-gradient(261.77deg, rgb(58, 80, 108) 15.4%, rgb(13, 34, 67) 100%)",
          }}
        >
          <div className="mb-[2px] font-bold text-[#FFFFFFD9]">
            환경부 전기차 충전카드 발급!
          </div>
          <div className="mb-6 font-extrabold text-xl text-white">
            내게 맞는 전기차 충전할인카드는?
          </div>
          <a
            className="bg-white rounded-lg w-fit px-4 py-2 font-semibold text-base text-[#191F28]"
            href="https://www.towncar.co.kr/post/best-charging-card-for-ev"
            target="_blank"
            rel="noopener noreferrer"
          >
            자세히 알아보기
          </a>
          <div className="absolute bottom-0 right-8 w-[150px] h-fit">
            <SVGCoupleUsingCharger style={{ width: "100%", height: "auto" }} />
          </div>
        </div>
        {/* 문의, 피드백, 링크공유 */}
        <div className="mb-14 flex w-full gap-6 justify-between">
          <div className="flex flex-1 justify-center items-center gap-2 rounded-[10px] bg-white py-3 font-bold text-[#191F28]">
            <a href="{()=>false}">서비스 새소식</a>
            <IconNews width={"1rem"} height={"1rem"} />
          </div>
          <div className="flex flex-1 justify-center items-center gap-2 rounded-[10px] bg-white py-3 font-bold text-[#191F28]">
            <a href="{()=>false}">서비스 피드백</a>
            <IconFeedback width={"1rem"} height={"1rem"} />
          </div>
          <div className="flex flex-1 justify-center items-center gap-2 rounded-[10px] bg-white py-3 font-bold text-[#191F28]">
            <a href="{()=>false}">서비스 링크 공유</a>
            <IconShare width={"1rem"} height={"1rem"} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Branding;
