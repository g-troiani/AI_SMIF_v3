import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface BacktestConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onBacktestComplete?: (plotUrl?: string, metrics?: any) => void;
}

const BacktestConfigModal: React.FC<BacktestConfigModalProps> = ({ isOpen, onClose, onBacktestComplete }) => {
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
    },
    stopLoss: '',
    takeProfit: ''
  });

  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetch('/api/backtest/strategies')
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            setStrategies(data.strategies);
          } else {
            console.error('Error fetching strategies:', data.message);
          }
        })
        .catch(error => {
          console.error('Error fetching strategies:', error);
        });
    }
  }, [isOpen]);

  const handleRunBacktest = () => {
    setIsRunning(true);
    const payload = {
      strategy: formData.strategy,
      symbol: formData.symbol,
      start_date: formData.dateRange.start,
      end_date: formData.dateRange.end,
      stop_loss: formData.stopLoss ? parseFloat(formData.stopLoss) : null,
      take_profit: formData.takeProfit ? parseFloat(formData.takeProfit) : null
    };

    fetch('/api/backtest/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    .then(res => res.json())
    .then(data => {
      setIsRunning(false);
      if (data.success) {
        // If backtest completed successfully, call onBacktestComplete if provided
        if (onBacktestComplete) {
          onBacktestComplete(data.plot_url, data.metrics);
        }
        // Close the modal automatically after success
        onClose();
      } else {
        console.error('Error running backtest:', data.message);
      }
    })
    .catch(err => {
      setIsRunning(false);
      console.error('Network error running backtest:', err);
    });
  };

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
          {isRunning && (
            <div className="text-center text-gray-700 mb-4">
              <span className="inline-block mr-2">Running backtest...</span>
              <div className="inline-block w-4 h-4 border-2 border-gray-300 border-t-transparent border-solid rounded-full animate-spin"></div>
            </div>
          )}

          {/* Form Fields */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Strategy</label>
              <select
                value={formData.strategy}
                onChange={e => setFormData({ ...formData, strategy: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="">Select a strategy</option>
                {strategies.map((strat, i) => (
                  <option key={i} value={strat}>{strat}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Symbol</label>
              <input
                type="text"
                value={formData.symbol}
                onChange={e => setFormData({ ...formData, symbol: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                placeholder="AAPL"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Start Date</label>
              <input
                type="date"
                value={formData.dateRange.start}
                onChange={e => setFormData({ ...formData, dateRange: { ...formData.dateRange, start: e.target.value } })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">End Date</label>
              <input
                type="date"
                value={formData.dateRange.end}
                onChange={e => setFormData({ ...formData, dateRange: { ...formData.dateRange, end: e.target.value } })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Stop Loss (%)</label>
              <input
                type="number"
                step="0.1"
                value={formData.stopLoss}
                onChange={e => setFormData({ ...formData, stopLoss: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Take Profit (%)</label>
              <input
                type="number"
                step="0.1"
                value={formData.takeProfit}
                onChange={e => setFormData({ ...formData, takeProfit: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              disabled={isRunning}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleRunBacktest}
              className={`px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${isRunning ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}`}
              disabled={isRunning}
            >
              {isRunning ? 'Running...' : 'Run Backtest'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BacktestConfigModal;
