// File: components/ui_module/frontend/src/pages/Strategy.tsx
// Type: tsx

import React, { useEffect, useState } from 'react';
import NewStrategyModal from '../components/NewStrategyModal';

interface StrategyItem {
  name: string;
  mode: 'backtest' | 'live';
}

const Strategy: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [strategies, setStrategies] = useState<StrategyItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/strategies')
      .then(res => res.json())
      .then(data => {
        if (data.success) setStrategies(data.data);
        else setError(data.message || 'Failed to fetch strategies');
      })
      .catch(err => {
        setError('Error fetching strategies');
        console.error(err);
      });
  }, []);

  const handleToggleMode = (strategy: StrategyItem) => {
    const newMode = strategy.mode === 'backtest' ? 'live' : 'backtest';

    fetch(`/api/strategies/${strategy.name}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: newMode })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setStrategies(prev =>
            prev.map(s => s.name === strategy.name
              ? { ...s, mode: newMode }
              : s
            )
          );
        } else {
          setError(data.message || 'Failed to update strategy mode');
        }
      })
      .catch(err => {
        setError('Network error updating strategy mode');
        console.error(err);
      });
  };

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Strategy Management</h2>
        <button 
          onClick={handleOpenModal}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
        >
          Add Strategy
        </button>
      </div>

      {error && <div className="text-red-600">{error}</div>}

      {/* For debugging or demonstration */}
      <div className="hidden">
        Modal state: {isModalOpen ? 'open' : 'closed'}
      </div>

      <NewStrategyModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />

      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Available Strategies
          </h3>
          {strategies.length === 0 ? (
            <div className="text-gray-500">
              No strategies configured
            </div>
          ) : (
            <ul className="space-y-2">
              {strategies.map((strat) => (
                <li key={strat.name} className="flex justify-between items-center">
                  <span className="font-semibold">{strat.name}</span>
                  <button
                    className={`px-3 py-1 rounded-md ${
                      strat.mode === 'live' ? 'bg-green-600 text-white' : 'bg-gray-300 text-black'
                    }`}
                    onClick={() => handleToggleMode(strat)}
                  >
                    {strat.mode === 'live' ? 'Switch to Backtest' : 'Switch to Live'}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default Strategy;