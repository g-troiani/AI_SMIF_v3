import React, { useState } from 'react';

const DataManagement: React.FC = () => {
  const [newTicker, setNewTicker] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  const handleAddTicker = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage(null);

    try {
      const response = await fetch('/api/tickers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ticker: newTicker.toUpperCase() }),
      });

      const data = await response.json();

      if (data.success) {
        setMessage({ type: 'success', text: `Successfully added ${newTicker.toUpperCase()}` });
        setNewTicker('');
      } else {
        setMessage({ type: 'error', text: data.message || 'Failed to add ticker' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Error connecting to server' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Data Management</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Data Configuration</h3>
          <form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Data Interval</label>
              <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                <option>5 Minutes</option>
                <option>15 Minutes</option>
                <option>1 Hour</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Historical Period</label>
              <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm">
                <option>5 Years</option>
              </select>
            </div>
            <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700">
              Update Configuration
            </button>
          </form>
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Data Status</h3>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">Last Update</p>
              <p className="font-medium">Never</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Stream Status</p>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                Inactive
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Ticker</h3>
        <form onSubmit={handleAddTicker} className="space-y-4">
          <div>
            <label htmlFor="ticker" className="block text-sm font-medium text-gray-700">
              Ticker Symbol
            </label>
            <div className="mt-1 flex rounded-md shadow-sm">
              <input
                type="text"
                name="ticker"
                id="ticker"
                value={newTicker}
                onChange={(e) => setNewTicker(e.target.value)}
                className="flex-1 min-w-0 block w-full px-3 py-2 rounded-md border-gray-300 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="AAPL"
                maxLength={5}
              />
              <button
                type="submit"
                disabled={isLoading || !newTicker}
                className="ml-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
              >
                {isLoading ? 'Adding...' : 'Add Ticker'}
              </button>
            </div>
          </div>
          {message && (
            <div className={`mt-2 text-sm ${message.type === 'success' ? 'text-green-600' : 'text-red-600'}`}>
              {message.text}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default DataManagement;