import React, { useState, useEffect } from 'react';

interface Position {
  symbol: string;
  qty: number;
  avgEntryPrice: number;
  marketValue: number;
  currentPrice: number;
  unrealizedPL: number;
  unrealizedPLPercent: number;
  change: number;
}

const CurrentPositions: React.FC = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPositions = async () => {
      try {
        const response = await fetch('/api/positions');
        const data = await response.json();
        
        if (data.success) {
          setPositions(data.positions);
        } else {
          setError(data.message);
        }
      } catch (err) {
        setError('Failed to fetch positions');
      } finally {
        setLoading(false);
      }
    };

    fetchPositions();
    const interval = setInterval(fetchPositions, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
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

  if (positions.length === 0) {
    return <div className="text-gray-500">No open positions</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
            <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
            <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Entry</th>
            <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Current</th>
            <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
            <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">P/L</th>
            <th scope="col" className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">%</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {positions.map((position) => (
            <tr key={position.symbol} className="hover:bg-gray-50">
              <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                {position.symbol}
              </td>
              <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-900">
                {position.qty.toLocaleString()}
              </td>
              <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-900">
                ${position.avgEntryPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </td>
              <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-900">
                ${position.currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </td>
              <td className="px-3 py-2 whitespace-nowrap text-sm text-right text-gray-900">
                ${position.marketValue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </td>
              <td className={`px-3 py-2 whitespace-nowrap text-sm text-right ${position.unrealizedPL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ${position.unrealizedPL.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </td>
              <td className={`px-3 py-2 whitespace-nowrap text-sm text-right ${position.unrealizedPLPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {position.unrealizedPLPercent >= 0 ? '+' : ''}
                {position.unrealizedPLPercent.toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CurrentPositions;