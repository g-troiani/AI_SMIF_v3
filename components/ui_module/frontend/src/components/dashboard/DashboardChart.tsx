import React, { useState } from 'react';
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

interface ChartData {
  history: Array<{
    date: string;
    value: number;
  }>;
  currentBalance: number;
  percentageChange: number;
}

// Time filter type
type TimeFilterOption = '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL';

// Custom tooltip component
const CustomTooltip = ({ active, payload, label, timeFilter }: any) => {
  if (!active || !payload || !payload.length) return null;

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

// Time filter component
const TimeFilter = ({ selected, onChange }: { selected: TimeFilterOption; onChange: (filter: TimeFilterOption) => void }) => {
  const options: TimeFilterOption[] = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];

  return (
    <div className="flex space-x-2">
      {options.map((period) => (
        <button
          key={period}
          onClick={() => onChange(period)}
          className={`px-3 py-1 text-sm rounded-full transition-colors ${
            selected === period 
              ? 'bg-green-600 text-white' 
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          {period}
        </button>
      ))}
    </div>
  );
};

// Portfolio summary component
const PortfolioSummary = ({ balance, percentageChange }: { balance: number; percentageChange: number }) => {
  return (
    <div>
      <p className="text-2xl font-semibold">{formatCurrency(balance)}</p>
      <p className={`text-sm ${percentageChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
        {percentageChange >= 0 ? '+' : ''}{percentageChange.toFixed(2)}%
      </p>
    </div>
  );
};

const DashboardChart: React.FC = () => {
  const [timeFilter, setTimeFilter] = useState<TimeFilterOption>('1M');
  const [data, setData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/portfolio/history?period=${timeFilter}`);
        const result = await response.json();
        
        if (result.success && result.data) {
          const validData = {
            ...result.data,
            history: result.data.history
              .filter((point: any) => 
                typeof point.value === 'number' && 
                !isNaN(point.value) && 
                point.value > 0
              )
              .map((point: any) => ({
                date: point.date,
                value: Number(point.value)
              }))
          };
          setData(validData);
          setError(null);
        } else {
          setError(result.message || 'Failed to fetch portfolio data');
        }
      } catch (error) {
        setError('Error fetching portfolio data');
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [timeFilter]);

  if (loading) {
    return <div className="h-64 flex items-center justify-center">Loading...</div>;
  }

  if (error) {
    return <div className="h-64 flex items-center justify-center text-red-500">{error}</div>;
  }

  if (!data || !data.history.length) {
    return <div className="h-64 flex items-center justify-center">No data available</div>;
  }

  return (
    <div className="p-6">
      <h3 className="text-lg font-medium leading-6 text-gray-900">Portfolio Performance</h3>
      
      <div className="mt-2">
        <PortfolioSummary 
          balance={data.currentBalance}
          percentageChange={data.percentageChange}
        />
      </div>

      <div className="mt-4">
        <TimeFilter 
          selected={timeFilter}
          onChange={setTimeFilter}
        />
      </div>

      <div className="mt-4" style={{ height: '400px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data.history}
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
              domain={['dataMin', 'dataMax']}
            />
            <Tooltip content={<CustomTooltip timeFilter={timeFilter} />} />
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
    </div>
  );
};

export default DashboardChart;