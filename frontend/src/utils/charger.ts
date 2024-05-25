/* 예상 충전완료 시각 (밀리초) */
export const calcChargeFinishTime = (startTime: number, output: number) => {
  const minTake = Math.floor((70 / (output * 0.8)) * 60);
  /* 충전시작시각이 20시간 전인 경우 갱신이 되지 않은 것으로 판단하고 대기시간을 0분으로 처리 */
  if (Math.abs(startTime - Date.now()) > 20 * 60 * 60 * 1000) return Date.now();
  return startTime + minTake * 60 * 1000;
};
