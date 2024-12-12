// src/components/dashboard/DashboardChart.tsx

import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip as ChartTooltip,
  TimeScale,
  Legend
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  ChartTooltip,
  TimeScale,
  Legend
);

// Define the structure of each data point
interface PortfolioData {
  date: string;
  value: number;
}

// Define the structure of the fetched data
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

  // Prepare Chart.js data
  const chartData = {
    labels: data.history.map(d => d.date),
    datasets: [
      {
        label: 'Portfolio Value',
        data: data.history.map(d => d.value),
        borderColor: data.percentageChange >= 0 ? '#16a34a' : '#dc2626',
        borderWidth: 2,
        pointRadius: 0,
        lineTension: 0.1
      }
    ]
  };

  // Determine min and max from data
  const values = data.history.map(d => d.value);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);

  // Chart.js configuration
  const options = {
    responsive: true,
    maintainAspectRatio: false as const,
    scales: {
      x: {
        type: 'time' as const,
        time: {
          unit: 'day'
        },
        ticks: {
          callback: function (value: any, index: number) {
            // The chart uses timestamps internally; format the label
            const labelDate = new Date((this.getLabelForValue(value) as string));
            return `${labelDate.getMonth() + 1}/${labelDate.getDate()}`;
          },
          color: '#4B5563',
        },
        grid: {
          color: 'rgba(0,0,0,0.05)'
        }
      },
      y: {
        suggestedMin: minVal,
        suggestedMax: maxVal,
        ticks: {
          callback: function(value: number) {
            return formatCurrency(value);
          },
          color: '#4B5563'
        },
        grid: {
          color: 'rgba(0,0,0,0.05)'
        }
      }
    },
    plugins: {
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const val = context.parsed.y;
            return `${formatCurrency(val)}`;
          },
          title: function(context: any) {
            if (context.length) {
              const dateStr = context[0].label;
              const date = new Date(dateStr);
              return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
            }
            return '';
          }
        }
      },
      legend: {
        display: false
      }
    }
  };

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
        <div className="w-full h-full">
          <Line data={chartData} options={options} />
        </div>
      </div>
    </div>
  );
};

export default DashboardChart;
