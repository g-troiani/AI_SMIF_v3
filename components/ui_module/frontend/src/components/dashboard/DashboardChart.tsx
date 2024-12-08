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

// Define the structure of each data point
interface PortfolioData {
  date: string;  // Format: 'YYYY-MM-DD'
  value: number; // Portfolio value on the given date
}

// Define the structure of the fetched data
interface ChartData {
  history: PortfolioData[];
  currentBalance: number;
  percentageChange: number;
}

const DashboardChart: React.FC = () => {
  // Define available time filters
  const timeFilters: Array<'1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL'> = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];
  
  // State to manage the selected time filter
  const [timeFilter, setTimeFilter] = useState<'1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL'>('1M');
  
  // State to manage fetched data
  const [data, setData] = useState<ChartData | null>(null);
  
  // Loading and error states
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data whenever the time filter changes
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`/api/portfolio/history?period=${timeFilter}`);
        const result = await response.json();
        if (result.success) {
          // Ensure that 'value' is a number
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

    // Optional: Polling every 60 seconds
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [timeFilter]);

  // Helper function to format currency
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  // Determine Y-axis domain based on data
  const getYAxisDomain = (history: PortfolioData[]): [number, number] => {
    const values = history.map(item => item.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.1; // 10% padding
    return [min - padding, max + padding];
  };

  // Generate Y-axis ticks (e.g., min, currentBalance, max)
  const getYAxisTicks = (min: number, max: number, currentBalance: number): number[] => {
    return [min, currentBalance, max];
  };

  // Render loading state
  if (loading) {
    return <div className="text-center">Loading...</div>;
  }

  // Render error state
  if (error) {
    return <div className="text-center text-red-500">{error}</div>;
  }

  // Render no data state
  if (!data || !data.history.length) {
    return <div className="text-center">No data available.</div>;
  }

  // Calculate Y-axis domain and ticks
  const yAxisDomain = getYAxisDomain(data.history);
  const yAxisTicks = getYAxisTicks(yAxisDomain[0], yAxisDomain[1], data.currentBalance);

  return (
    <div>
      {/* Current Balance and Percentage Change */}
      <div className="mt-2">
        <p className="text-2xl font-semibold">{formatCurrency(data.currentBalance)}</p>
        <p className={`text-sm ${data.percentageChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
          {data.percentageChange >= 0 ? '+' : ''}
          {data.percentageChange.toFixed(2)}%
        </p>
      </div>

      {/* Time Filter Buttons */}
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

      {/* Line Chart */}
      <div className="h-64 mt-4">
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
                // Format as MM/DD
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }}
              stroke="#4B5563" // Gray-700
            />
            <YAxis
              domain={yAxisDomain}
              ticks={yAxisTicks}
              tickFormatter={(value: number) => formatCurrency(value)}
              stroke="#4B5563" // Gray-700
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
              stroke="#3b82f6" // Blue-500
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
