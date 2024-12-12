// src/components/dashboard/DashboardChart.tsx

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

interface PortfolioData {
  date: string;  
  value: number; 
}

interface ChartData {
  history: PortfolioData[];
  currentBalance: number;
  percentageChange: number;
}

const DashboardChart: React.FC = () => {
  const timeFilters: Array<'1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL'> = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];
  const [timeFilter, setTimeFilter] = useState<'1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL'>('1M');
  const [data, setData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/portfolio/history?period=${timeFilter}`);
        const result = await response.json();
        if (result.success) {
          const processedData: ChartData = {
            history: result.data.history.map((item: any) => ({
              date: item.date,
              value: Number(item.value)
            })),
            currentBalance: Number(result.data.currentBalance),
            percentageChange: Number(result.data.percentageChange)
          };
          setData(processedData);
        } else {
          setError('Failed to fetch data.');
        }
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('An error occurred while fetching data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [timeFilter]);

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  if (loading) {
    return <div className="text-center">Loading...</div>;
  }

  if (error) {
    return <div className="text-center text-red-500">{error}</div>;
  }

  if (!data || !data.history.length) {
    return <div className="text-center">No data available.</div>;
  }

  return (
    <div>
      <div className="mt-2">
        <p className="text-2xl font-semibold">{formatCurrency(data.currentBalance)}</p>
        <p className={`text-sm ${data.percentageChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
          {data.percentageChange >= 0 ? '+' : ''}
          {data.percentageChange.toFixed(2)}%
        </p>
      </div>

      <div className="flex space-x-2 mt-4">
        {timeFilters.map((period) => (
          <button
            key={period}
            onClick={() => setTimeFilter(period)}
            className={`px-3 py-1 text-sm rounded-full transition-colors ${
              timeFilter === period
                ? 'bg-green-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            {period}
          </button>
        ))}
      </div>

      <div className="h-64 mt-4 flex justify-center items-center">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data.history}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={(dateStr: string) => {
                const date = new Date(dateStr);
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
              stroke="#4B5563"
            />
            <YAxis
              domain={['dataMin', 'dataMax']}
              tickFormatter={(value: number) => formatCurrency(value)}
              stroke="#4B5563"
            />
            <Tooltip
              formatter={(value: number) => formatCurrency(value)}
              labelFormatter={(label: string) => {
                const date = new Date(label);
                return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={data.percentageChange >= 0 ? "#16a34a" : "#dc2626"}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DashboardChart;
