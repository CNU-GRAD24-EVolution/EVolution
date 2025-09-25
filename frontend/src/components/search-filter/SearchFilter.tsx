import FilterItem from "./FilterItem";

const FILTER_CATEGORIES = [
  {
    type: "chargerTypes",
    title: "충전기 타입",
    options: [
      { id: "01", label: "DC차데모" },
      { id: "02", label: "AC완속" },
      { id: "04", label: "DC콤보" },
      { id: "07", label: "AC3상" },
    ],
  },
  {
    type: "minOutput",
    title: "속도",
    options: [
      { id: "3", label: "3kW 이상" },
      { id: "7", label: "7kW 이상" },
      { id: "50", label: "50kW 이상" },
      { id: "100", label: "100kW 이상" },
      { id: "200", label: "200kW 이상" },
    ],
  },
  {
    type: "parkingFree",
    title: "무료주차 여부",
    options: [
      { id: "Y", label: "Y" },
      { id: "N", label: "N" },
    ],
  },
];

/** 주변 충전소 검색 필터 */
const SearchFilter = () => {
  return (
    <div className="flex gap-2 w-full">
      {FILTER_CATEGORIES.map((category) => (
        <FilterItem category={category} key={category.type} />
      ))}
    </div>
  );
};

export default SearchFilter;
