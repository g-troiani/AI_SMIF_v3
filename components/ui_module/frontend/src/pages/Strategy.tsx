// File: components/ui_module/frontend/src/pages/Strategy.tsx
import React, { useEffect, useState } from 'react';
import NewStrategyModal from '../components/NewStrategyModal';

// For storing the numeric fields in the main data
interface StrategyItem {
  name: string;
  mode: 'backtest' | 'live';
  allocation: number;    // e.g. 1234.56 means $1,234.56
  stop_loss: number;     // e.g. 0.05 => 5%
  take_profit: number;   // e.g. 0.1 => 10%
  tickers: string;       // plain text
}

function parseCurrency(str: string): number {
  const cleaned = str.replace(/[^0-9.\-]+/g, '');
  return parseFloat(cleaned) || 0;
}
function formatCurrency(val: number): string {
  return val.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });
}

function parsePercent(str: string): number {
  const cleaned = str.replace(/[^0-9.\-]+/g, '');
  return (parseFloat(cleaned) || 0) / 100;
}
function formatPercent(val: number): string {
  return (val * 100).toFixed(2) + '%';
}

const Strategy: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [strategies, setStrategies] = useState<StrategyItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  // --- Local ephemeral states for user-typing text (indexed by strategy row) ---
  // We store each numeric input’s typed text, so we can let the user type freely,
  // then parse/format on blur.
  const [localAllocations, setLocalAllocations] = useState<string[]>([]);
  const [localStopLosses, setLocalStopLosses] = useState<string[]>([]);
  const [localTakeProfits, setLocalTakeProfits] = useState<string[]>([]);

  useEffect(() => {
    fetch('/api/strategies')
      .then((res) => res.json())
      .then((data) => {
        if (!data.success) {
          setError(data.message || 'Failed to fetch strategies');
          return;
        }

        // Convert backend data to numeric fields
        const loaded: StrategyItem[] = data.data.map((s: any) => ({
          name: s.name,
          mode: s.mode,
          allocation: s.allocation ? parseFloat(s.allocation) : 0,
          stop_loss: s.stop_loss ? parseFloat(s.stop_loss) : 0,
          take_profit: s.take_profit ? parseFloat(s.take_profit) : 0,
          tickers: s.tickers || '',
        }));

        setStrategies(loaded);

        // Initialize ephemeral text states with a formatted string
        setLocalAllocations(
          loaded.map((st) => formatCurrency(st.allocation))
        );
        setLocalStopLosses(
          loaded.map((st) => formatPercent(st.stop_loss))
        );
        setLocalTakeProfits(
          loaded.map((st) => formatPercent(st.take_profit))
        );
      })
      .catch((err) => {
        setError('Error fetching strategies');
        console.error(err);
      });
  }, []);

  // Handler for Tickers can remain in the main strategies array
  const handleTickersChange = (index: number, newVal: string) => {
    setStrategies((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], tickers: newVal };
      return copy;
    });
  };

  // ========== ALLOCATION INPUTS ==========
  const handleAllocationChange = (index: number, newText: string) => {
    // user is typing text freely
    setLocalAllocations((prev) => {
      const copy = [...prev];
      copy[index] = newText;
      return copy;
    });
  };
  const handleAllocationBlur = (index: number) => {
    // parse typed => numeric => store in strategies
    const rawNum = parseCurrency(localAllocations[index]);
    setStrategies((prev) => {
      const copy = [...prev];
      copy[index].allocation = rawNum;
      return copy;
    });
    // also reformat ephemeral text
    setLocalAllocations((prev) => {
      const copy = [...prev];
      copy[index] = formatCurrency(rawNum);
      return copy;
    });
  };
  const handleAllocationFocus = (index: number) => {
    // On focus, show plain numeric to user
    const rawNum = parseCurrency(localAllocations[index]);
    setLocalAllocations((prev) => {
      const copy = [...prev];
      copy[index] = String(rawNum || '');
      return copy;
    });
  };

  // ========== STOP LOSS INPUTS ==========
  const handleStopLossChange = (index: number, newText: string) => {
    setLocalStopLosses((prev) => {
      const copy = [...prev];
      copy[index] = newText;
      return copy;
    });
  };
  const handleStopLossBlur = (index: number) => {
    const val = parsePercent(localStopLosses[index]);
    setStrategies((prev) => {
      const copy = [...prev];
      copy[index].stop_loss = val;
      return copy;
    });
    setLocalStopLosses((prev) => {
      const copy = [...prev];
      copy[index] = formatPercent(val);
      return copy;
    });
  };
  const handleStopLossFocus = (index: number) => {
    const val = parsePercent(localStopLosses[index]);
    setLocalStopLosses((prev) => {
      const copy = [...prev];
      copy[index] = String(val * 100 || '');
      return copy;
    });
  };

  // ========== TAKE PROFIT INPUTS ==========
  const handleTakeProfitChange = (index: number, newText: string) => {
    setLocalTakeProfits((prev) => {
      const copy = [...prev];
      copy[index] = newText;
      return copy;
    });
  };
  const handleTakeProfitBlur = (index: number) => {
    const val = parsePercent(localTakeProfits[index]);
    setStrategies((prev) => {
      const copy = [...prev];
      copy[index].take_profit = val;
      return copy;
    });
    setLocalTakeProfits((prev) => {
      const copy = [...prev];
      copy[index] = formatPercent(val);
      return copy;
    });
  };
  const handleTakeProfitFocus = (index: number) => {
    const val = parsePercent(localTakeProfits[index]);
    setLocalTakeProfits((prev) => {
      const copy = [...prev];
      copy[index] = String(val * 100 || '');
      return copy;
    });
  };

  // Toggle mode => PATCH request
  const handleToggleMode = (index: number) => {
    const strat = strategies[index];
    const newMode = strat.mode === 'backtest' ? 'live' : 'backtest';

    fetch(`/api/strategies/${strat.name}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mode: newMode,
        allocation: strat.allocation,
        stop_loss: strat.stop_loss,
        take_profit: strat.take_profit,
        tickers: strat.tickers,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data.success) {
          setError(data.message || 'Failed to update strategy');
          return;
        }
        // locally update mode
        setStrategies((prev) => {
          const copy = [...prev];
          copy[index] = { ...copy[index], mode: newMode };
          return copy;
        });
      })
      .catch((err) => {
        setError('Network error updating strategy mode');
        console.error(err);
      });
  };

  const handleOpenModal = () => setIsModalOpen(true);

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

      <div className="hidden">Modal state: {isModalOpen ? 'open' : 'closed'}</div>

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
            <div className="text-gray-500">No strategies configured</div>
          ) : (
            <ul className="space-y-4">
              {strategies.map((strat, i) => (
                <li key={strat.name} className="bg-gray-50 p-3 rounded">
                  <div className="grid grid-cols-1 gap-2">
                    <div className="text-lg font-semibold">
                      {strat.name}
                    </div>
                    <div className="grid grid-cols-5 items-center gap-4">
                      {/* Allocation */}
                      <div className="flex items-center space-x-2">
                        <label className="whitespace-nowrap">Allocation:</label>
                        <input
                          type="text"
                          className="border px-1 py-0.5 w-24"
                          onFocus={() => handleAllocationFocus(i)}
                          onBlur={() => handleAllocationBlur(i)}
                          onChange={(e) =>
                            handleAllocationChange(i, e.target.value)
                          }
                          value={localAllocations[i] ?? ''}
                        />
                      </div>

                      {/* Stop Loss */}
                      <div className="flex items-center space-x-2">
                        <label className="whitespace-nowrap">Stop Loss:</label>
                        <input
                          type="text"
                          className="border px-1 py-0.5 w-20"
                          onFocus={() => handleStopLossFocus(i)}
                          onBlur={() => handleStopLossBlur(i)}
                          onChange={(e) =>
                            handleStopLossChange(i, e.target.value)
                          }
                          value={localStopLosses[i] ?? ''}
                        />
                      </div>

                      {/* Take Profit */}
                      <div className="flex items-center space-x-2">
                        <label className="whitespace-nowrap">Take Profit:</label>
                        <input
                          type="text"
                          className="border px-1 py-0.5 w-20"
                          onFocus={() => handleTakeProfitFocus(i)}
                          onBlur={() => handleTakeProfitBlur(i)}
                          onChange={(e) =>
                            handleTakeProfitChange(i, e.target.value)
                          }
                          value={localTakeProfits[i] ?? ''}
                        />
                      </div>

                      {/* Tickers */}
                      <div className="flex items-center space-x-2">
                        <label className="whitespace-nowrap">Tickers:</label>
                        <input
                          type="text"
                          className="border px-1 py-0.5 w-32"
                          placeholder="AAPL,TSLA"
                          value={strat.tickers}
                          onChange={(e) =>
                            handleTickersChange(i, e.target.value)
                          }
                        />
                      </div>

                      {/* Toggle Mode */}
                      <div className="justify-self-end">
                        <button
                          className={`px-3 py-1 rounded-md ${
                            strat.mode === 'live'
                              ? 'bg-green-600 text-white'
                              : 'bg-gray-300 text-black'
                          }`}
                          onClick={() => handleToggleMode(i)}
                        >
                          {strat.mode === 'live'
                            ? 'Switch to Backtest'
                            : 'Switch to Live'}
                        </button>
                      </div>
                    </div>
                  </div>
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
