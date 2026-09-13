import React, { useState } from 'react';
import './BankCard.css';

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

const BankCard: React.FC<BankCardProps> = ({
  cardNumber = '**** **** **** 1234',
  holderName = 'NOMBRE DEL TITULAR',
  expiryDate = 'MM/YY',
  bankName = 'Banorte',
  balance = '$0.00',
  currency = 'MXN',
  cardType = 'debit',
  additionalInfo = [],
  accessibilityLabel = 'Tarjeta bancaria'
}) => {
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
      className={`bank-card-container ${isExpanded ? 'expanded' : ''}`}
      role="button"
      tabIndex={0}
      aria-expanded={isExpanded}
      aria-label={`${accessibilityLabel}. ${isExpanded ? 'Información detallada visible' : 'Haz clic para ver información detallada'}`}
      onClick={toggleExpand}
      onKeyDown={handleKeyDown}
    >
      <div className="bank-card">
        {/* Parte frontal de la tarjeta */}
        <div className="card-front">
          <div className="card-header">
            <div className="bank-logo">{bankName}</div>
            <div className="card-type-icon">
              {cardType === 'credit' ? '💳' : '🏦'}
            </div>
          </div>
          
          <div className="card-chip"></div>
          
          <div className="card-number">
            {formatCardNumber(cardNumber)}
          </div>
          
          <div className="card-details-row">
            <div className="card-holder">
              <span className="label">Titular</span>
              <span className="value">{holderName.toUpperCase()}</span>
            </div>
            <div className="card-expiry">
              <span className="label">Expira</span>
              <span className="value">{expiryDate}</span>
            </div>
          </div>
          
          <div className="card-balance">
            <span className="balance-label">Saldo disponible</span>
            <span className="balance-amount">{balance}</span>
            {currency && <span className="currency">{currency}</span>}
          </div>
        </div>

        {/* Parte trasera / Información expandida */}
        {isExpanded && (
          <div className="card-back" aria-live="polite">
            <div className="expand-indicator">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 15l-6-6-6 6"/>
              </svg>
              <span>Ver menos</span>
            </div>
            
            {additionalInfo.length > 0 && (
              <div className="additional-info">
                <h4>Información Adicional</h4>
                <ul>
                  {additionalInfo.map((info, index) => (
                    <li key={index}>
                      <span className="info-label">{info.label}:</span>
                      <span className="info-value">{info.value}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="card-security-note">
              <small>🔒 Información segura. Haz clic en la tarjeta para ocultar los detalles.</small>
            </div>
          </div>
        )}
        
        {!isExpanded && (
          <div className="expand-hint">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6"/>
            </svg>
            <span>Clic para ver detalles</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default BankCard;
