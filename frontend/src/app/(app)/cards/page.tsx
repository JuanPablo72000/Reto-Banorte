"use client";

// Tarjetas: REST /me/credit-cards renderizadas con BankCard (la misma del
// plan IA) + tabla de límites. Fallback: tarjeta demo y bloque IA.

import { useAuth } from "@/components/auth/AuthProvider";
import BankCard from "@/components/BankCard";
import { CainQuery } from "@/components/chat/CainQuery";
import { formatCurrency } from "@/components/balance/types";
import { Card } from "@/components/ui/Card";
import { DemoBadge } from "@/components/ui/DemoBadge";
import { Icon } from "@/components/ui/Icon";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { LoadingState } from "@/components/states/LoadingState";
import { EmptyState } from "@/components/states/EmptyState";
import { apiGet, type CreditCardResponse } from "@/lib/api/backend";
import { useBackendData } from "@/lib/hooks/useBackendData";

const TARJETA_DEMO: CreditCardResponse = {
    idCreditCard: 0,
    cardNumberMasked: "**** **** **** 4821",
    cardType: "credit",
    creditLimit: 35000,
    availableCredit: 21750.5,
    interestRate: 4.5,
    statementCutOffDay: 15,
    paymentDueDay: 5,
    status: "active",
    createdAt: new Date().toISOString(),
};

export default function CardsPage() {
    const { session } = useAuth();
    const { data, cargando, noDisponible } = useBackendData(
        () => apiGet<CreditCardResponse[]>("/me/credit-cards", session?.token),
        [session],
    );

    const tarjetas = data && data.length > 0 ? data : noDisponible ? [TARJETA_DEMO] : (data ?? []);
    const demo = noDisponible || !data || data.length === 0;

    return (
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h2 className="text-xl font-semibold text-[var(--color-text)]">Tarjetas</h2>
                    <p className="text-sm text-[var(--color-text-muted)]">
                        Crédito disponible, cortes y pagos de tus tarjetas.
                    </p>
                </div>
                <DemoBadge activo={demo} />
            </header>

            {cargando && !data ? (
                <LoadingState message="Cargando tarjetas…" variant="skeleton" />
            ) : tarjetas.length === 0 ? (
                <EmptyState
                    title="Sin tarjetas"
                    description="Todavía no tienes tarjetas registradas. Consulta al asistente."
                    icon={<Icon name="card" size={40} />}
                />
            ) : (
                <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-2">
                    {tarjetas.map((t, i) => {
                        const usado = t.creditLimit - t.availableCredit;
                        const porcentaje = t.creditLimit > 0 ? (usado / t.creditLimit) * 100 : 0;
                        return (
                            <div key={t.idCreditCard} className="ui-rise flex flex-col gap-4" style={{ "--orden": i + 1 } as React.CSSProperties}>
                                <BankCard
                                    cardNumber={t.cardNumberMasked}
                                    holderName={session?.user.name ?? "Titular"}
                                    expiryDate="12/29"
                                    bankName="Banorte"
                                    balance={formatCurrency(t.availableCredit)}
                                    currency="MXN"
                                    cardType="credit"
                                    additionalInfo={[
                                        { label: "Línea de crédito", value: formatCurrency(t.creditLimit) },
                                        { label: "Pago mínimo", value: `Día ${t.paymentDueDay}` },
                                    ]}
                                    accessibilityLabel={`Tarjeta de crédito ${t.cardNumberMasked}, disponible ${formatCurrency(t.availableCredit)} de ${formatCurrency(t.creditLimit)}`}
                                />
                                <Card className="card-hover flex flex-col gap-3">
                                    <ProgressBar
                                        value={porcentaje}
                                        label="Crédito utilizado"
                                        tone={porcentaje > 80 ? "danger" : porcentaje > 50 ? "warning" : "success"}
                                    />
                                    <div className="grid grid-cols-3 gap-2 text-center text-sm">
                                        <div>
                                            <p className="text-xs text-[var(--color-text-muted)]">Disponible</p>
                                            <p className="font-semibold tabular-nums text-[var(--color-text)]">{formatCurrency(t.availableCredit)}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--color-text-muted)]">Corte</p>
                                            <p className="font-semibold text-[var(--color-text)]">Día {t.statementCutOffDay}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--color-text-muted)]">Tasa</p>
                                            <p className="font-semibold tabular-nums text-[var(--color-text)]">{t.interestRate}%</p>
                                        </div>
                                    </div>
                                </Card>
                            </div>
                        );
                    })}
                </div>
            )}

            <Card className="ui-rise flex flex-col gap-3" style={{ "--orden": 4 } as React.CSSProperties}>
                <div className="flex items-center gap-2">
                    <Icon name="sparkle" size={18} className="text-[var(--color-accent)]" />
                    <h3 className="text-sm font-semibold text-[var(--color-text)]">Asistente inteligente</h3>
                </div>
                <CainQuery label="Consultar mis tarjetas" tool="get_credit_cards" icon="card" titulo="Tarjetas con IA" />
            </Card>
        </div>
    );
}
