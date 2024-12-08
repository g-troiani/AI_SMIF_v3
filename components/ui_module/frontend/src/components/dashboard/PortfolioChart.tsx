import React, { useState, useEffect } from 'react';

interface ChartData {
  history: Array<{
    date: string;
    value: number;
  }>;
  currentBalance: number;
  percentageChange: number;
}

const DashboardChart: React.FC = () => {
  const [timeFilter, setTimeFilter] = useState<'1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL'>('1M');
  const [data, setData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/portfolio/history?period=${timeFilter}`);
        const result = await response.json();
        if (result.success) {
          setData(result.data);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [timeFilter]);

  if (loading || !data) {
    return <div className="h-64 flex items-center justify-center">Loading...</div>;
  }

  // Calculate percentages for heights
  const minValue = Math.min(...data.history.map(d => d.value));
  const maxValue = Math.max(...data.history.map(d => d.value));
  const valueRange = maxValue - minValue;

  const getHeight = (value: number) => {
    return ((value - minValue) / valueRange) * 100;
  };

  return (
    <div className="p-6">
      <h3 className="text-lg font-medium leading-6 text-gray-900">Portfolio Performance</h3>
      
      <div className="mt-2">
        <p className="text-2xl font-semibold">${data.currentBalance.toFixed(2)}</p>
        <p className={`text-sm ${data.percentageChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
          {data.percentageChange >= 0 ? '+' : ''}{data.percentageChange.toFixed(2)}%
        </p>
      </div>

      <div className="flex space-x-2 mt-4">
        {['1D', '1W', '1M', '3M', '1Y', 'ALL'].map((period) => (
          <button
            key={period}
            onClick={() => setTimeFilter(period as typeof timeFilter)}
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

      {/* Chart Container */}
      <div className="mt-4 h-64 relative">
        {/* Step bars */}
        <div className="flex h-full">
          {data.history.map((point, index) => (
            <div 
              key={index} 
              className="flex-1 bg-transparent hover:bg-gray-100 group relative"
              style={{ height: '100%' }}
            >
              {/* The actual bar */}
              <div 
                className="absolute bottom-0 w-full bg-blue-500"
                style={{ height: `${getHeight(point.value)}%` }}
              />
              
              {/* Tooltip */}
              <div className="hidden group-hover:block absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 p-2 bg-white rounded shadow-lg z-10 whitespace-nowrap">
                <p className="font-semibold">${point.value.toFixed(2)}</p>
                <p className="text-sm text-gray-500">
                  {new Date(point.date).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardChart;