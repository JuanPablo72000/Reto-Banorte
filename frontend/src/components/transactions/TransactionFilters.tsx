"use client";

import { Select } from "@/components/ui/Select";
import { Input } from "@/components/ui/Input";
import {
    TransactionFiltersState,
    TRANSACTION_ACCOUNTS,
    CATEGORY_LABELS,
} from "./types";

export interface TransactionFiltersProps {
    value: TransactionFiltersState;
    onChange: (next: TransactionFiltersState) => void;
}

export function TransactionFilters({ value, onChange }: TransactionFiltersProps) {
    function update<K extends keyof TransactionFiltersState>(
        key: K,
        newValue: TransactionFiltersState[K]
    ) {
        onChange({ ...value, [key]: newValue });
    }

    return (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <Select
                label="Cuenta"
                value={value.accountId}
                onChange={(e) => update("accountId", e.target.value)}
                options={[
                    { value: "all", label: "Todas las cuentas" },
                    ...TRANSACTION_ACCOUNTS.map((acc) => ({
                        value: acc.id,
                        label: acc.alias,
                    })),
                ]}
            />

            <Select
                label="Dirección"
                value={value.direction}
                onChange={(e) =>
                    update("direction", e.target.value as TransactionFiltersState["direction"])
                }
                options={[
                    { value: "all", label: "Todas" },
                    { value: "in", label: "Entrada" },
                    { value: "out", label: "Salida" },
                ]}
            />

            <Select
                label="Categoría"
                value={value.category}
                onChange={(e) =>
                    update("category", e.target.value as TransactionFiltersState["category"])
                }
                options={[
                    { value: "all", label: "Todas" },
                    ...Object.entries(CATEGORY_LABELS).map(([val, label]) => ({
                        value: val,
                        label,
                    })),
                ]}
            />

            <Input
                label="Desde"
                type="date"
                value={value.dateFrom}
                onChange={(e) => update("dateFrom", e.target.value)}
            />

            <Input
                label="Hasta"
                type="date"
                value={value.dateTo}
                onChange={(e) => update("dateTo", e.target.value)}
            />
        </div>
    );
}