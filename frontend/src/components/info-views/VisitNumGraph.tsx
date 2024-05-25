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

/** 임시 더미데이터 */
const data = [
  {
    name: "0",
    amt: 1,
  },
  {
    name: "1",
    amt: 1,
  },
  {
    name: "2",
    amt: 1,
  },
  {
    name: "3",
    amt: 2,
  },
  {
    name: "4",
    amt: 2,
  },
  {
    name: "5",
    amt: 2,
  },
  {
    name: "6",
    amt: 1,
  },
  {
    name: "7",
    amt: 1,
  },
  {
    name: "8",
    amt: 1,
  },
  {
    name: "9",
    amt: 1,
  },
  {
    name: "10",
    amt: 0,
  },
  {
    name: "11",
    amt: 0,
  },
  {
    name: "12",
    amt: 1,
  },
  {
    name: "13",
    amt: 1,
  },
  {
    name: "14",
    amt: 2,
  },
  {
    name: "15",
    amt: 1,
  },
  {
    name: "16",
    amt: 1,
  },
  {
    name: "17",
    amt: 1,
  },
  {
    name: "18",
    amt: 1,
  },
  {
    name: "19",
    amt: 1,
  },
  {
    name: "20",
    amt: 2,
  },
  {
    name: "21",
    amt: 2,
  },
  {
    name: "22",
    amt: 3,
  },
  {
    name: "23",
    amt: 3,
  },
];

const VisitNumGraph = () => {
  return (
    <ResponsiveContainer width="100%" aspect={4.0 / 2.5}>
      <LineChart
        data={data}
        margin={{ top: 10, right: 10, left: -30, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="2 2" />
        <XAxis dataKey="name" interval={5} fontSize="0.75rem" />
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
          dataKey="amt"
          name="이용객수"
          stroke="#bc73e9"
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default VisitNumGraph;
