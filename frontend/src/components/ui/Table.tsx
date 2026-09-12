import { ReactNode } from "react";

export interface TableColumn<T> {
    key: string;
    header: string;
    render?: (row: T) => ReactNode;
    align?: "left" | "right" | "center";
}

export interface TableProps<T> {
    columns: TableColumn<T>[];
    data: T[];
    getRowId: (row: T) => string | number;
    caption?: string;
}

const alignClasses = {
    left: "text-left",
    right: "text-right",
    center: "text-center",
};

export function Table<T>({ columns, data, getRowId, caption }: TableProps<T>) {
    return (
        <div className="overflow-x-auto rounded-lg border border-[var(--color-border)]">
            <table className="w-full border-collapse text-sm">
                {caption && <caption className="sr-only">{caption}</caption>}
                <thead>
                <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface-2)]">
                    {columns.map((col) => (
                        <th
                            key={col.key}
                            scope="col"
                            className={[
                                "px-4 py-3 font-medium text-[var(--color-text)]",
                                alignClasses[col.align ?? "left"],
                            ].join(" ")}
                        >
                            {col.header}
                        </th>
                    ))}
                </tr>
                </thead>
                <tbody>
                {data.map((row) => (
                    <tr
                        key={getRowId(row)}
                        className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-surface-2)]"
                    >
                        {columns.map((col) => (
                            <td
                                key={col.key}
                                className={[
                                    "px-4 py-3 text-[var(--color-text)]",
                                    alignClasses[col.align ?? "left"],
                                ].join(" ")}
                            >
                                {col.render ? col.render(row) : String((row as Record<string, unknown>)[col.key] ?? "")}
                            </td>
                        ))}
                    </tr>
                ))}
                </tbody>
            </table>

            {data.length === 0 && (
                <p className="p-6 text-center text-sm text-[var(--color-text-muted)]">Sin datos para mostrar</p>
            )}
        </div>
    );
}