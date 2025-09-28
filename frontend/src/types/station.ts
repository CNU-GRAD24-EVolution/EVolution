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
  };
  demandInfo: {
    viewNum: number;
    departsIn30m: Date[];
    hourlyVisitNum: number[];
  } | null;
  lastUpdateTime: string;
  statId: string;
}

export interface ChargerStatus {
  statId: string;
  chgerId: string;
  chgerType: string;
  stat: string;
  statUpdDt: string | null;
  lastTsdt: string | null;
  lastTedt: string | null;
  nowTsdt: string | null;
  output: string | null;
  method: string | null;
  delYn: string;
  delDetail: string | null;
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
  demandInfo: {
    viewNum: number;
    departsIn30m: Date[];
    hourlyVisitNum: number[];
  } | null;
  lastUpdateTime: string;
  statId: string;
}
