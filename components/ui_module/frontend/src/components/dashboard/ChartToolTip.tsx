import React from 'react';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<any>;
  label?: string;
  timeFilter: string;
}

const ChartTooltip: React.FC<ChartTooltipProps> = ({ active, payload, label, timeFilter }) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  return (
    <div className="bg-white p-3 border rounded shadow-lg">
      <p className="font-semibold text-gray-900">
        {formatCurrency(payload[0].value)}
      </p>
      <p className="text-sm text-gray-500">
        {formatDate(label, timeFilter === '1D')}
      </p>
    </div>
  );
};

export default ChartTooltip;