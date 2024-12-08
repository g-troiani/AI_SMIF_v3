import React, { useState } from 'react';
import BacktestConfigModal from '../components/BacktestConfigModal';

const Backtest: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Backtest</h2>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
        >
          New Backtest
        </button>
      </div>

      <BacktestConfigModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />

      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <div className="flex space-x-4 mb-6">
            <button className="text-gray-600 hover:text-gray-900">Backtest Guide</button>
            <button className="text-gray-600 hover:text-gray-900">Custom Strategy</button>
            <button className="text-gray-600 hover:text-gray-900">Troubleshooting</button>
          </div>

          <div className="relative">
            <input
              type="text"
              placeholder="Search backtests..."
              className="w-full px-4 py-2 border border-gray-300 rounded-md"
            />
          </div>

          <table className="min-w-full mt-4">
            <thead>
              <tr>
                <th className="text-left">Date</th>
                <th className="text-left">Strategy</th>
                <th className="text-left">Symbol</th>
                <th className="text-left">Return</th>
                <th className="text-left">Trades</th>
              </tr>
            </thead>
            <tbody>
              {/* Backtest results will be listed here */}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Backtest;