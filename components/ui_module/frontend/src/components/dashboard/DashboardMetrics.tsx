// src/components/dashboard/DashboardMetrics.tsx

import React, { useState, useEffect } from 'react';

interface DashboardData {
  account_balance: number;
  cash_available: number;
  today_pl: number;
  today_return: number;
}

const DashboardMetrics: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      console.log("Fetching dashboard data...");
      try {
        const response = await fetch('/api/dashboard-data');
        console.log("Received response:", response);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error("Non-OK response:", response.status, errorText);
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log("Parsed JSON result:", result);
        
        if (result.success) {
          console.log("Dashboard data fetched successfully:", result.data);
          setData(result.data);
        } else {
          console.error("API returned success=false with message:", result.message);
          setError(result.message || 'Failed to fetch data');
        }
      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setError('Failed to fetch dashboard data');
      } finally {
        setLoading(false);
        console.log("Loading state set to false");
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-4 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-6 bg-gray-200 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-800 p-4 rounded-lg">
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!data) return null;

  const metrics = [
    {
      title: 'Account Balance',
      value: `$${data.account_balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      className: 'text-gray-900'
    },
    {
      title: 'Cash Available',
      value: `$${data.cash_available.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      className: 'text-gray-900'
    },
    {
      title: "Today's P/L",
      value: `$${data.today_pl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      className: data.today_pl >= 0 ? 'text-green-600' : 'text-red-600'
    },
    {
      title: "Today's Return",
      value: `${data.today_return >= 0 ? '+' : ''}${data.today_return.toFixed(2)}%`,
      className: data.today_return >= 0 ? 'text-green-600' : 'text-red-600'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, index) => (
        <div key={index} className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-500">{metric.title}</h3>
          <p className={`mt-1 text-xl font-semibold ${metric.className}`}>
            {metric.value}
          </p>
        </div>
      ))}
    </div>
  );
};

export default DashboardMetrics;
