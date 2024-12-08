import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface BacktestConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const BacktestConfigModal: React.FC<BacktestConfigModalProps> = ({ isOpen, onClose }) => {
  const [strategies, setStrategies] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    strategy: '',
    symbol: '',
    dateRange: {
      start: '',
      end: ''
    },
    tradingHours: {
      start: '09:30',
      end: '16:00'
    }
  });

  // Fetch available strategies when modal opens
  useEffect(() => {
    if (isOpen) {
      console.log('Fetching strategies...');
      fetch('/api/strategies')
        .then(response => response.json())
        .then(data => {
          console.log('Received strategies:', data);
          setStrategies(Object.keys(data));
        })
        .catch(error => {
          console.error('Error fetching strategies:', error);
        });
    }
  }, [isOpen]);

  // Add another useEffect to monitor strategies state
  useEffect(() => {
    console.log('Current strategies in state:', strategies);
  }, [strategies]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Configure Backtest</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Strategy</label>
              <select 
                value={formData.strategy}
                onChange={(e) => setFormData(prev => ({ ...prev, strategy: e.target.value }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="">Select a strategy</option>
                {strategies.map(strategy => (
                  <option key={strategy} value={strategy}>
                    {strategy.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Symbol</label>
              <input
                type="text"
                placeholder="e.g., AAPL"
                value={formData.symbol}
                onChange={(e) => setFormData(prev => ({ ...prev, symbol: e.target.value }))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Date Range</label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="date"
                  value={formData.dateRange.start}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    dateRange: { ...prev.dateRange, start: e.target.value }
                  }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
                <input
                  type="date"
                  value={formData.dateRange.end}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    dateRange: { ...prev.dateRange, end: e.target.value }
                  }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Trading Hours</label>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="time"
                  value={formData.tradingHours.start}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    tradingHours: { ...prev.tradingHours, start: e.target.value }
                  }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
                <input
                  type="time"
                  value={formData.tradingHours.end}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    tradingHours: { ...prev.tradingHours, end: e.target.value }
                  }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="button"
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
            >
              Run Backtest
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BacktestConfigModal;