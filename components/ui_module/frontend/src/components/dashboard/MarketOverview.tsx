import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, ResponsiveContainer } from 'recharts';

interface TrendPoint {
  time: string;
  price: number;
}

interface MarketItem {
  symbol: string;
  name: string;
  price: number | string; // Adjusted to allow string for BTC
  change: number;
  trend: TrendPoint[];
  exchange?: string; // If you added exchange info on the backend
}

const MarketOverview: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string|null>(null);

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        const response = await fetch('/api/market-overview');
        const result = await response.json();

        if (result.success) {
          // result.data should be an array of MarketItem
          setMarketData(result.data);
        } else {
          setError(result.message);
        }
      } catch (err) {
        console.error('Error fetching market data:', err);
        setError('Failed to fetch market data');
      } finally {
        setLoading(false);
      }
    };

    fetchMarketData();
    const interval = setInterval(fetchMarketData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
        <div className="flex items-center justify-center h-40">
          <p className="text-gray-500">Loading market data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-lg">
        <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
        <div className="text-red-500">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
      <div className="space-y-2">
        {marketData.map((item) => {
          // Handle formatting of the price
          let priceDisplay: string;
          if (typeof item.price === 'number') {
            priceDisplay = item.price.toFixed(2);
          } else {
            // If it's a string (like BTC), just use it as is
            // Assuming BTC is formatted from backend as a string with commas, etc.
            priceDisplay = item.price;
          }

          // Determine line color for trend
          // If trend is available and has more than one point, check first/last to determine up or down
          let lineColor = '#16a34a'; // green by default
          if (item.trend && item.trend.length > 1) {
            const firstPrice = item.trend[0].price;
            const lastPrice = item.trend[item.trend.length - 1].price;
            if (lastPrice < firstPrice) {
              lineColor = '#dc2626'; // red if price went down
            }
          }

          return (
            <div key={item.symbol} className="flex items-center space-x-4 p-2 rounded-lg">
              <div className="flex-1">
                <h3 className="text-md font-medium text-gray-900">{item.name}</h3>
                <p className="text-sm text-gray-500">{item.symbol}</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-gray-900">${priceDisplay}</p>
                <p className={`text-sm ${item.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {(item.change >= 0 ? '+' : '')}{item.change.toFixed(2)}%
                </p>
              </div>
              <div style={{ width: 80, height: 40 }} className="flex justify-center items-center">
                {item.trend && item.trend.length > 0 && (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={item.trend} margin={{ top: 5, right: 5, bottom: 5, left: 5 }}>
                      <XAxis dataKey="time" hide={true} padding={{ left: 10, right: 10 }} />
                      <Line type="monotone" dataKey="price" stroke={lineColor} strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MarketOverview;
