"use client";

import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { LineChart } from "@/components/ui/Chart";
import { AccountBalance, formatCurrency } from "./types";

interface BalanceCardProps {
    account: AccountBalance;
}

export function BalanceCard({ account }: BalanceCardProps) {
    const isLow = account.currentBalance <= 0;

    return (
        <Card>
            <CardHeader>
                <CardTitle>{account.label}</CardTitle>
            </CardHeader>

            <div className="flex flex-col gap-3 p-4">
                <div className="flex items-center justify-between">
          <span className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            {account.accountNumber}
          </span>
                    {isLow && <Badge>Sin fondos</Badge>}
                </div>

                <p className="text-2xl font-semibold">
                    {formatCurrency(account.currentBalance, account.currency)}
                </p>

                <LineChart
                    data={account.trend}
                    xKey="day"
                    yKey="balance"
                    height={140}
                />
            </div>
        </Card>
    );
}