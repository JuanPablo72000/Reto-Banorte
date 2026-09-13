"use client";

import { Table } from "@/components/ui/Table";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { lista } from "@/lib/plan-result";

interface Categoria {
    id_category: number;
    name: string;
    code: string;
    icon?: string | null;
}

// get_expense_categories (table).
export function ExpenseCategoriesList({ step }: { step: ExecutedStep }) {
    const rows = lista<Categoria>(step.result);
    return (
        <Table
            caption="Categorías de gasto"
            columns={[
                { key: "name", header: "Categoría", render: (c) => c.name },
            ]}
            data={rows}
            getRowId={(c) => c.id_category}
        />
    );
}
