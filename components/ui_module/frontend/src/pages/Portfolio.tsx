import React from 'react';
import CurrentPositions from '../components/portfolio/CurrentPositions';
import RecentTrades from '../components/portfolio/RecentTrades';

const Portfolio: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Portfolio</h2>
        <div className="space-x-4">
          <button className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700">
            New Trade
          </button>
          <button className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700">
            Emergency Liquidation
          </button>
        </div>
      </div>

      <div className="flex flex-col space-y-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Current Positions</h3>
          <CurrentPositions />
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Trades</h3>
          <RecentTrades />
        </div>
      </div>
    </div>
  );
};

export default Portfolio;