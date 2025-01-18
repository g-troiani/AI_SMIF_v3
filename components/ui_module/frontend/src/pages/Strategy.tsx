// File: components/strategy_management_module/strategies/Strategy.tsx
// (Or wherever your "Strategy.tsx" currently resides.)

import React, { useEffect, useState } from 'react';
import NewStrategyModal from '../components/NewStrategyModal';

interface StrategyItem {
  name: string;
  mode: 'live' | 'backtest';
  allocation: number; 
  stop_loss: number;
  take_profit: number;
  tickers: string;    
  timeframe: string;  
}

function parseCurrency(str: string): number {
  const cleaned = str.replace(/[^0-9.\-]+/g, '');
  return parseFloat(cleaned) || 0;
}
function formatCurrency(val: number): string {
  return val.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
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

  const [localAllocations, setLocalAllocations] = useState<string[]>([]);
  const [localStopLosses, setLocalStopLosses] = useState<string[]>([]);
  const [localTakeProfits, setLocalTakeProfits] = useState<string[]>([]);
  const [localTimeframes, setLocalTimeframes] = useState<string[]>([]);

  useEffect(() => {
    fetch('/api/strategies')
      .then((res) => res.json())
      .then((data) => {
        if (!data.success) {
          setError(data.message || 'Failed to fetch strategies');
          return;
        }

        const loaded: StrategyItem[] = data.data.map((s: any) => ({
          name: s.name,
          mode: s.mode,
          allocation: s.allocation ? parseFloat(s.allocation) : 0,
          stop_loss: s.stop_loss ? parseFloat(s.stop_loss) : 0,
          take_profit: s.take_profit ? parseFloat(s.take_profit) : 0,
          tickers: Array.isArray(s.tickers) ? s.tickers.join(',') : s.tickers || '',
          timeframe: '5Min' //s.timeframe || '1Min',
        }));
        setStrategies(loaded);

        setLocalAllocations(loaded.map((st) => formatCurrency(st.allocation)));
        setLocalStopLosses(loaded.map((st) => formatPercent(st.stop_loss)));
        setLocalTakeProfits(loaded.map((st) => formatPercent(st.take_profit)));
        setLocalTimeframes(loaded.map((st) => st.timeframe));
      })
      .catch((err) => {
        setError('Error fetching strategies');
        console.error(err);
      });
  }, []);

  const handleTickersChange = (index: number, newVal: string) => {
    setStrategies((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], tickers: newVal };
      return copy;
    });
  };

  // ----- Allocation handlers -----
  const handleAllocationChange = (index: number, newText: string) => {
    setLocalAllocations((prev) => {
      const copy = [...prev];
      copy[index] = newText;
      return copy;
    });
  };
  const handleAllocationBlur = (index: number) => {
    const rawNum = parseCurrency(localAllocations[index]);
    setStrategies((prev) => {
      const copy = [...prev];
      copy[index].allocation = rawNum;
      return copy;
    });
    setLocalAllocations((prev) => {
      const copy = [...prev];
      copy[index] = formatCurrency(rawNum);
      return copy;
    });
  };
  const handleAllocationFocus = (index: number) => {
    const rawNum = parseCurrency(localAllocations[index]);
    setLocalAllocations((prev) => {
      const copy = [...prev];
      copy[index] = String(rawNum || '');
      return copy;
    });
  };

  // ----- Stop Loss handlers -----
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

  // ----- Take Profit handlers -----
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

  // ----- Timeframe handlers -----
  const handleTimeframeChange = (index: number, newVal: string) => {
    setLocalTimeframes((prev) => {
      const copy = [...prev];
      copy[index] = newVal;
      return copy;
    });
    setStrategies((prev) => {
      const copy = [...prev];
      copy[index].timeframe = newVal;
      return copy;
    });
  };

  // ----- Toggle mode -----
  const handleToggleMode = (index: number) => {
    const strat = strategies[index];
    const newMode = strat.mode === 'live' ? 'backtest' : 'live';

    // Add client‐side logging around the fetch request
    console.log('[Toggle Mode] Sending PATCH request for strategy:', strat.name);

    fetch(`/api/strategies/${strat.name}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mode: newMode,
        allocation: strat.allocation,
        stop_loss: strat.stop_loss,
        take_profit: strat.take_profit,
        tickers: strat.tickers.split(',').map(s => s.trim()),
        timeframe: strat.timeframe
      }),
    })
      .then((res) => {
        console.log('[Toggle Mode] Received status:', res.status);
        return res.json();
      })
      .then((data) => {
        console.log('[Toggle Mode] Response payload:', data);
        if (!data.success) {
          setError(data.message || 'Failed to update strategy');
          return;
        }
        setStrategies((prev) => {
          const copy = [...prev];
          copy[index].mode = newMode;
          return copy;
        });
      })
      .catch((err) => {
        setError(`Network error updating strategy mode: ${err}`);
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
                    {/* Show the strategy name.  */}
                    <div className="text-lg font-semibold">{strat.name}</div>

                    {/* Row with Allocation, StopLoss, TP, Tickers, Timeframe, Toggle */}
                    <div className="grid grid-cols-6 items-center gap-4">
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

                      {/* Timeframe */}
                      <div className="flex items-center space-x-2">
                        <label className="whitespace-nowrap">Timeframe:</label>
                        <select
                          className="border px-1 py-1"
                          value={localTimeframes[i]}
                          onChange={(e) => handleTimeframeChange(i, e.target.value)}
                        >
                          <option value="1Min">1Min</option>
                          <option value="5Min">5Min</option>
                          <option value="15Min">15Min</option>
                          <option value="1Hour">1Hour</option>
                          <option value="1Day">1Day</option>
                        </select>
                      </div>

                      {/* Toggle Mode */}
                      <div className="justify-self-end">
                        {strat.mode === 'live' ? (
                          <button
                            className="px-3 py-1 rounded-md bg-green-600 text-white"
                            onClick={() => handleToggleMode(i)}
                          >
                            LIVE
                            <span className="ml-2 text-sm font-medium">
                              Switch to Backtest
                            </span>
                          </button>
                        ) : (
                          <button
                            className="px-3 py-1 rounded-md bg-gray-300 text-black"
                            onClick={() => handleToggleMode(i)}
                          >
                            BACKTEST
                            <span className="ml-2 text-sm font-medium">
                              Switch to Live
                            </span>
                          </button>
                        )}
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
