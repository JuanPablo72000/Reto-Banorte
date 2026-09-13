"use client";

import { useState } from "react";
import styles from "./BankCard.module.css";
import { Icon } from "@/components/ui/Icon";

interface BankCardProps {
  cardNumber?: string;
  holderName?: string;
  expiryDate?: string;
  bankName?: string;
  balance?: string;
  currency?: string;
  cardType?: 'debit' | 'credit';
  additionalInfo?: {
    label: string;
    value: string;
  }[];
  accessibilityLabel?: string;
}

export default function BankCard({
  cardNumber = '**** **** **** 1234',
  holderName = 'NOMBRE DEL TITULAR',
  expiryDate = 'MM/YY',
  bankName = 'Banorte',
  balance = '$0.00',
  currency = 'MXN',
  cardType = 'debit',
  additionalInfo = [],
  accessibilityLabel = 'Tarjeta bancaria'
}: BankCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleExpand();
    }
  };

  // Formato parcial del número de tarjeta
  const formatCardNumber = (number: string) => {
    if (number.includes('****')) return number;
    return `**** **** **** ${number.slice(-4)}`;
  };

  return (
    <div
      className={`${styles['bank-card-container']} ${isExpanded ? styles.expanded : ''}`}
      role="button"
      tabIndex={0}
      aria-expanded={isExpanded}
      aria-label={`${accessibilityLabel}. ${isExpanded ? 'Información detallada visible' : 'Haz clic para ver información detallada'}`}
      onClick={toggleExpand}
      onKeyDown={handleKeyDown}
    >
      <div className={styles['bank-card']}>
        {/* Parte frontal de la tarjeta */}
        <div className={styles['card-front']}>
          <div className={styles['card-header']}>
            <div className={styles['bank-logo']}>{bankName}</div>
            <div className={styles['card-type-icon']} aria-hidden="true">
              <Icon name={cardType === 'credit' ? 'card' : 'account'} size={28} />
            </div>
          </div>

          <div className={styles['card-chip']} aria-hidden="true"></div>

          <div className={styles['card-number']}>
            {formatCardNumber(cardNumber)}
          </div>

          <div className={styles['card-details-row']}>
            <div className={styles['card-holder']}>
              <span className={styles.label}>Titular</span>
              <span className={styles.value}>{holderName.toUpperCase()}</span>
            </div>
            <div className={styles['card-expiry']}>
              <span className={styles.label}>Expira</span>
              <span className={styles.value}>{expiryDate}</span>
            </div>
          </div>

          <div className={styles['card-balance']}>
            <span className={styles['balance-label']}>Saldo disponible</span>
            <span className={styles['balance-amount']}>{balance}</span>
            {currency && <span className={styles.currency}>{currency}</span>}
          </div>
        </div>

        {/* Parte trasera / Información expandida */}
        {isExpanded && (
          <div className={styles['card-back']} aria-live="polite">
            <div className={styles['expand-indicator']}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M18 15l-6-6-6 6"/>
              </svg>
              <span>Ver menos</span>
            </div>

            {additionalInfo.length > 0 && (
              <div className={styles['additional-info']}>
                <h4>Información Adicional</h4>
                <ul>
                  {additionalInfo.map((info, index) => (
                    <li key={index}>
                      <span className={styles['info-label']}>{info.label}:</span>
                      <span className={styles['info-value']}>{info.value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className={styles['card-security-note']}>
              <small>
                <Icon name="lock" size={14} /> Información segura. Haz clic en la tarjeta para ocultar los detalles.
              </small>
            </div>
          </div>
        )}

        {!isExpanded && (
          <div className={styles['expand-hint']} aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
            <span>Clic para ver detalles</span>
          </div>
        )}
      </div>
    </div>
  );
}
