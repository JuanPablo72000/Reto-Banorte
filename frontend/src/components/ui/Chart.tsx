import {
    Bar,
    BarChart as ReBarChart,
    CartesianGrid,
    Cell,
    Line,
    LineChart as ReLineChart,
    Pie,
    PieChart as RePieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

export interface ChartDatum {
    [key: string]: string | number;
}

interface BaseChartProps {
    data: ChartDatum[];
    xKey: string;
    yKey: string;
    height?: number;
    color?: string;
}

const DEFAULT_COLOR = "var(--color-accent)";
const DONUT_COLORS = [
    "var(--color-accent)",
    "var(--color-safe)",
    "var(--color-accent-dark)",
    "var(--color-accent-soft)",
    "var(--color-warning-bg)",
    "var(--color-text-muted)",
];

const TOOLTIP_STYLE: React.CSSProperties = {
    background: "var(--color-surface-2)",
    border: "1px solid var(--color-border)",
    borderRadius: "0.5rem",
    color: "var(--color-text)",
    fontSize: "0.8125rem",
};

export function LineChart({ data, xKey, yKey, height = 240, color = DEFAULT_COLOR }: BaseChartProps) {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <ReLineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey={xKey} tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} dot={false} />
            </ReLineChart>
        </ResponsiveContainer>
    );
}

export function BarChart({ data, xKey, yKey, height = 240, color = DEFAULT_COLOR }: BaseChartProps) {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <ReBarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey={xKey} tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" />
                <YAxis tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
            </ReBarChart>
        </ResponsiveContainer>
    );
}

interface DonutChartProps {
    data: ChartDatum[];
    nameKey: string;
    valueKey: string;
    height?: number;
}

export function DonutChart({ data, nameKey, valueKey, height = 240 }: DonutChartProps) {
    return (
        <ResponsiveContainer width="100%" height={height}>
            <RePieChart>
                <Pie
                    data={data}
                    dataKey={valueKey}
                    nameKey={nameKey}
                    innerRadius="60%"
                    outerRadius="85%"
                    paddingAngle={2}
                >
                    {data.map((_, index) => (
                        <Cell key={index} fill={DONUT_COLORS[index % DONUT_COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
            </RePieChart>
        </ResponsiveContainer>
    );
}