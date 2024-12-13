import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { formatCurrency, formatDate } from '../../utils/formatters';
import ChartTooltip from './ChartTooltip';

interface PortfolioChartProps {
  data: Array<{ date: string; value: number }>;
  timeFilter: string;
}

const PortfolioChart: React.FC<PortfolioChartProps> = ({ data, timeFilter }) => {
  return (
    <div style={{ height: '400px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 30, left: 10, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid 
            strokeDasharray="3 3" 
            vertical={false}
            stroke="#E5E7EB"
          />
          <XAxis
            dataKey="date"
            tickFormatter={(date) => formatDate(date, timeFilter === '1D')}
            tick={{ fill: '#6B7280', fontSize: 12 }}
            axisLine={{ stroke: '#E5E7EB' }}
            tickLine={{ stroke: '#E5E7EB' }}
          />
          <YAxis
            tickFormatter={formatCurrency}
            tick={{ fill: '#6B7280', fontSize: 12 }}
            axisLine={{ stroke: '#E5E7EB' }}
            tickLine={{ stroke: '#E5E7EB' }}
            width={80}
          />
          <Tooltip content={<ChartTooltip timeFilter={timeFilter} />} />
          <Area
            type="monotone"
            dataKey="value"
            stroke="#22c55e"
            fillOpacity={1}
            fill="url(#colorValue)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PortfolioChart;