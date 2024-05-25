/** datetime으로부터 경과한 시간을 문자열로 표현하여 반환 */
export const calcElaspedTime = (datetime: number): string => {
  const start = new Date(datetime);
  const end = new Date();

  const seconds = Math.floor(Math.abs(end.getTime() - start.getTime()) / 1000);

  const minutes = seconds / 60;
  if (minutes < 60) return `${Math.floor(minutes)}분`;

  const hours = minutes / 60;
  if (hours < 24)
    return `${Math.floor(hours)}시간 ${Math.floor(
      minutes - Math.floor(hours) * 60
    )}분`;

  const days = hours / 24;
  if (days) return `${Math.floor(days)}일`;

  return `${start.toLocaleDateString()}`;
};

/** yyyyMMddHHmmss 포맷의 시간을 밀리초 숫자(From 1970-1-1)로 변환 */
export const yyyyMMddHHmmssToDateTime = (datetime: string): number => {
  return new Date(
    datetime.replace(
      /^(\d{4})(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)$/,
      "$4:$5:$6 $2/$3/$1"
    )
  ).getTime();
};
