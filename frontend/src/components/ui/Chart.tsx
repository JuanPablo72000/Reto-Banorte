import {
    Area,
    AreaChart as ReAreaChart,
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
    /** Serie única opcional; si se omite, se grafican TODAS las claves
     *  numéricas como series (multi-barra/multi-línea), en orden. */
    yKey?: string;
    height?: number;
    color?: string;
}

// Colores de la paleta activa (respetan daltonismo/mono/oscuro).
export const SERIES_COLORS = [
    "var(--color-accent)",
    "var(--color-safe)",
    "var(--color-accent-dark)",
    "var(--color-accent-soft)",
    "var(--color-warning-bg)",
    "var(--color-text-muted)",
];

const DONUT_COLORS = SERIES_COLORS;

const TOOLTIP_STYLE: React.CSSProperties = {
    background: "var(--color-surface-2)",
    border: "1px solid var(--color-border)",
    borderRadius: "0.5rem",
    color: "var(--color-text)",
    fontSize: "0.8125rem",
};

/** Detecta las series numéricas de los datos (excluye la clave de etiquetas). */
function seriesDe(data: ChartDatum[], xKey: string, yKey?: string): string[] {
    if (yKey) return [yKey];
    const primera = data[0] ?? {};
    return Object.keys(primera).filter((k) => k !== xKey && typeof primera[k] === "number");
}

function Ejes({ xKey }: { xKey: string }) {
    return (
        <>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" />
            <YAxis tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" width={56} />
        </>
    );
}

export function LineChart({ data, xKey, yKey, height = 240, color }: BaseChartProps) {
    const series = seriesDe(data, xKey, yKey);
    return (
        <ResponsiveContainer width="100%" height={height}>
            <ReLineChart data={data}>
                <Ejes xKey={xKey} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                {series.map((s, i) => (
                    <Line
                        key={s}
                        type="monotone"
                        dataKey={s}
                        stroke={color ?? SERIES_COLORS[i % SERIES_COLORS.length]}
                        strokeWidth={2}
                        dot={false}
                        isAnimationActive
                    />
                ))}
            </ReLineChart>
        </ResponsiveContainer>
    );
}

export function AreaChart({ data, xKey, yKey, height = 240, color }: BaseChartProps) {
    const series = seriesDe(data, xKey, yKey);
    return (
        <ResponsiveContainer width="100%" height={height}>
            <ReAreaChart data={data}>
                <Ejes xKey={xKey} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                {series.map((s, i) => (
                    <Area
                        key={s}
                        type="monotone"
                        dataKey={s}
                        stroke={color ?? SERIES_COLORS[i % SERIES_COLORS.length]}
                        fill={color ?? SERIES_COLORS[i % SERIES_COLORS.length]}
                        fillOpacity={0.18}
                        strokeWidth={2}
                        isAnimationActive
                    />
                ))}
            </ReAreaChart>
        </ResponsiveContainer>
    );
}

export function BarChart({ data, xKey, yKey, height = 240, color }: BaseChartProps) {
    const series = seriesDe(data, xKey, yKey);
    return (
        <ResponsiveContainer width="100%" height={height}>
            <ReBarChart data={data}>
                <Ejes xKey={xKey} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: "var(--color-surface-2)" }} />
                {series.map((s, i) => (
                    <Bar
                        key={s}
                        dataKey={s}
                        fill={color ?? SERIES_COLORS[i % SERIES_COLORS.length]}
                        radius={[4, 4, 0, 0]}
                        isAnimationActive
                    />
                ))}
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
                    isAnimationActive
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
