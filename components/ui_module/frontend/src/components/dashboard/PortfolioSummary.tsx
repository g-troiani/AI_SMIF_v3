import React from 'react';
import { formatCurrency } from '../../utils/formatters';

interface PortfolioSummaryProps {
  balance: number;
  percentageChange: number;
}

const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({ balance, percentageChange }) => {
  return (
    <div>
      <p className="text-2xl font-semibold">{formatCurrency(balance)}</p>
      <p className={`text-sm ${percentageChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
        {percentageChange >= 0 ? '+' : ''}{percentageChange.toFixed(2)}%
      </p>
    </div>
  );
};

export default PortfolioSummary;