import {
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  Line,
  ResponsiveContainer,
} from "recharts";

/** 지난 30일동안의 충전이력을 기반으로 예측한 금일 이용객수 그래프
 * @prop data: 시간별 예상이용객수를 담은 배열 (0시 ~ 23시)
 */
const VisitNumGraph = ({ data }: { data: number[] }) => {
  /** 시간별 예상이용객수를 그래프 데이터 포맷으로 변환 */
  const items = data.map((v, idx) => ({ name: Number(idx), visitNum: v }));

  return (
    <ResponsiveContainer width="100%" aspect={4.0 / 2.5}>
      <LineChart
        data={items}
        margin={{ top: 20, right: 10, left: -30, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="2 2" />
        <XAxis
          dataKey="name"
          interval={5}
          fontSize="0.75rem"
          tickFormatter={(tickItem) => `${tickItem}시`}
        />
        <YAxis
          allowDecimals={false}
          interval={1}
          fontSize="0.75rem"
          tickFormatter={(tickItem) => `${tickItem}명`}
        />
        <Tooltip
          formatter={(v, n) => [`${v}명`, `${n}`]}
          labelFormatter={(time) => time + "시"}
          labelStyle={{ fontSize: "0.75rem" }}
          contentStyle={{ fontSize: "0.75rem" }}
        />
        {/* 범례 */}
        <Legend wrapperStyle={{ fontSize: "0.75rem", marginLeft: 20 }} />
        <Line
          type="monotone"
          dataKey="visitNum"
          name="이용객수"
          stroke="#bc73e9"
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default VisitNumGraph;
