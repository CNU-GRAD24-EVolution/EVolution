// 간략한 정보만을 포함한 단일 충전소 데이터
// 충전소의 각 충전기 데이터는 상세정보에만 포함
export interface StationSummarized {
  info: {
    chargerTypes: string[];
    lat: string;
    lng: string;
    maxOutput: string;
    parkingFree: string;
    statNm: string;
    useTime: string;
    totalChargers: number;
    usableChargers: number;
    usingChargers: number;
    // visitNumNextHour: number;
  };
  lastUpdateTime: string;
  statId: string;
}

export interface ChargerStatus {
  statId: string;
  chgerId: string;
  chgerType: string;
  stat: string;
  statUpdDt: string;
  lastTsdt: string;
  lastTedt: string;
  nowTsdt: string;
  output: string;
  method: string;
  delYn: string;
  delDetail: string;
}

// 상세정보를 포함한 단일 충전소 데이터
export interface StationDetailed {
  // 충전소의 각 충전기 상태 데이터
  chargers: ChargerStatus[];
  info: {
    totalChargers: number;
    usableChargers: number;
    usingChargers: number;
    // visitNumNextHour: number;
    chargerTypes: string[];
    maxOutput: string;
    statNm: string;
    addr: string;
    location: string;
    useTime: string;
    lat: string;
    lng: string;
    busiId: string;
    bnm: string;
    busiNm: string;
    busiCall: string;
    zcode: string;
    zscode: string;
    kind: string;
    kindDetail: string;
    parkingFree: string;
    note: string;
    limitYn: string;
    limitDetail: string;
    trafficYn: string;
  };
  lastUpdateTime: string;
  statId: string;
}
