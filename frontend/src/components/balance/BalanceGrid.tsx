"use client";

import { BalanceCard } from "./BalanceCard";
import { MOCK_BALANCES } from "./types";

export function BalanceGrid() {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {MOCK_BALANCES.map((account) => (
                <BalanceCard key={account.id} account={account} />
            ))}
        </div>
    );
}