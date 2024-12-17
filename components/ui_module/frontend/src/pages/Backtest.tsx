// import React, { useState, useEffect } from 'react';
// import BacktestConfigModal from '../components/BacktestConfigModal';

// interface BacktestMetrics {
//   strategy_name: string;
//   ticker: string;
//   start_date: string;
//   end_date: string;
//   cagr: number;
//   total_return_pct: number;
//   std_dev: number | null;
//   annual_vol: number | null;
//   sharpe_ratio: number | null;
//   sortino_ratio: number | null;
//   max_drawdown: number | null;
//   win_rate: number | null;
//   num_trades: number | null;
//   information_ratio: number | null;
//   strategy_unique_id: string;
// }

// const Backtest: React.FC = () => {
//   const [isModalOpen, setIsModalOpen] = useState(false);
//   const [plotUrl, setPlotUrl] = useState<string | null>(null);
//   const [backtestResults, setBacktestResults] = useState<BacktestMetrics[]>([]);

//   // Adjust handleBacktestComplete to accept optional metrics
//   const handleBacktestComplete = (url?: string, metrics?: BacktestMetrics) => {
//     if (url) setPlotUrl(url);
//     if (metrics) {
//       setBacktestResults(prev => [...prev, metrics]);
//     }
//   };

//   useEffect(() => {
//     // If needed, we can load previously saved results here
//   }, []);

//   return (
//     <div className="space-y-6">
//       <div className="flex justify-between items-center">
//         <h2 className="text-2xl font-bold text-gray-900">Backtest</h2>
//         <button 
//           onClick={() => setIsModalOpen(true)}
//           className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700"
//         >
//           New Backtest
//         </button>
//       </div>

//       <BacktestConfigModal 
//         isOpen={isModalOpen}
//         onClose={() => setIsModalOpen(false)}
//         onBacktestComplete={handleBacktestComplete}
//       />

//       <div className="bg-white shadow rounded-lg">
//         <div className="p-6">
//           <div className="flex space-x-4 mb-6">
//             <button className="text-gray-600 hover:text-gray-900">Backtest Guide</button>
//             <button className="text-gray-600 hover:text-gray-900">Custom Strategy</button>
//             <button className="text-gray-600 hover:text-gray-900">Troubleshooting</button>
//           </div>

//           <div className="relative">
//             <input
//               type="text"
//               placeholder="Search backtests..."
//               className="w-full px-4 py-2 border border-gray-300 rounded-md"
//             />
//           </div>

//           <table className="min-w-full mt-4">
//             <thead>
//               <tr>
//                 <th className="text-left">Date</th>
//                 <th className="text-left">Strategy</th>
//                 <th className="text-left">Symbol</th>
//                 <th className="text-left">Return</th>
//                 <th className="text-left">Trades</th>
//               </tr>
//             </thead>
//             <tbody>
//               {/* If you want a quick summary per result, map them here */}
//             </tbody>
//           </table>
//         </div>
//       </div>

//       <h2 className="text-2xl font-bold text-gray-900">Backtest Results</h2>
//       {plotUrl && (
//         <div>
//           <h3 className="text-lg font-medium text-gray-900 mb-4">Backtest Chart</h3>
//           <img src={plotUrl} alt="Backtest Plot" className="border rounded shadow-lg max-w-full" />
//         </div>
//       )}

//       {/* Scrollable table for all metrics */}
//       <div className="overflow-x-auto border border-gray-200 rounded-lg">
//         <table className="min-w-max text-sm text-left whitespace-nowrap">
//           <thead className="bg-gray-50">
//             <tr>
//               <th className="px-4 py-2">Strategy Name</th>
//               <th className="px-4 py-2">Ticker</th>
//               <th className="px-4 py-2">Start Date</th>
//               <th className="px-4 py-2">End Date</th>
//               <th className="px-4 py-2">CAGR</th>
//               <th className="px-4 py-2">Total Return %</th>
//               <th className="px-4 py-2">Std Dev</th>
//               <th className="px-4 py-2">Annual Vol</th>
//               <th className="px-4 py-2">Sharpe Ratio</th>
//               <th className="px-4 py-2">Sortino Ratio</th>
//               <th className="px-4 py-2">Max Drawdown</th>
//               <th className="px-4 py-2">Win Rate</th>
//               <th className="px-4 py-2"># of Trades</th>
//               <th className="px-4 py-2">Information Ratio</th>
//               <th className="px-4 py-2">Strategy Unique ID</th>
//             </tr>
//           </thead>
//           <tbody>
//             {backtestResults.map((res, i) => (
//               <tr key={i} className="border-t">
//                 <td className="px-4 py-2">{res.strategy_name}</td>
//                 <td className="px-4 py-2">{res.ticker}</td>
//                 <td className="px-4 py-2">{res.start_date}</td>
//                 <td className="px-4 py-2">{res.end_date}</td>
//                 <td className="px-4 py-2">{(res.cagr * 100).toFixed(2)}%</td>
//                 <td className="px-4 py-2">{res.total_return_pct.toFixed(2)}%</td>
//                 <td className="px-4 py-2">{res.std_dev !== null ? res.std_dev.toFixed(4) : 'N/A'}</td>
//                 <td className="px-4 py-2">{res.annual_vol !== null ? res.annual_vol.toFixed(4) : 'N/A'}</td>
//                 <td className="px-4 py-2">{res.sharpe_ratio !== null ? res.sharpe_ratio.toFixed(2) : 'N/A'}</td>
//                 <td className="px-4 py-2">{res.sortino_ratio !== null ? res.sortino_ratio.toFixed(2) : 'N/A'}</td>
//                 <td className="px-4 py-2">{res.max_drawdown !== null ? `${res.max_drawdown.toFixed(2)}%` : 'N/A'}</td>
//                 <td className="px-4 py-2">{res.win_rate !== null ? `${res.win_rate.toFixed(2)}%` : 'N/A'}</td>
//                 <td className="px-4 py-2">{res.num_trades !== null ? res.num_trades : 'N/A'}</td>
//                 <td className="px-4 py-2">{res.information_ratio !== null ? res.information_ratio.toFixed(2) : 'N/A'}</td>
//                 <td className="px-4 py-2">{res.strategy_unique_id}</td>
//               </tr>
//             ))}
//           </tbody>
//         </table>
//       </div>
//     </div>
//   );
// };

// export default Backtest;



import React, { useState, useEffect } from 'react';
import BacktestConfigModal from '../components/BacktestConfigModal';

interface BacktestMetrics {
  strategy_name: string;
  ticker: string;
  start_date: string;
  end_date: string;
  cagr: number;
  total_return_pct: number;
  std_dev: number | null;
  annual_vol: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown: number | null;
  win_rate: number | null;
  num_trades: number | null;
  information_ratio: number | null;
  strategy_unique_id: string;
}

const Backtest: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [plotUrl, setPlotUrl] = useState<string | null>(null);
  const [backtestResults, setBacktestResults] = useState<BacktestMetrics[]>([]);

  // If you have an API endpoint that returns a list of previous backtests, you can fetch it here
  // If not, you can comment out this useEffect until you have that endpoint implemented.
  useEffect(() => {
    // Example: If you have /api/backtests returning { success: boolean, results: BacktestMetrics[] }
    // If this endpoint does not exist yet, comment out or remove this fetch call.
    fetch('/api/backtests')
      .then((res) => res.json())
      .then((data) => {
        if (data.success && Array.isArray(data.results)) {
          setBacktestResults(data.results);
        }
      })
      .catch((error) => {
        console.error('Error fetching backtests:', error);
      });
  }, []);

  const handleBacktestComplete = (url?: string, metrics?: BacktestMetrics) => {
    if (url) setPlotUrl(url);

    // If you want to re-fetch results after a backtest is completed:
    // Again, ensure that the /api/backtests endpoint exists in your backend.
    fetch('/api/backtests')
      .then((res) => res.json())
      .then((data) => {
        if (data.success && Array.isArray(data.results)) {
          setBacktestResults(data.results);
        }
      })
      .catch((error) => {
        console.error('Error fetching backtests after completion:', error);
      });

    // If you don't have an /api/backtests endpoint, just append the metrics to local state:
    // if (metrics) {
    //   setBacktestResults(prev => [...prev, metrics]);
    // }
  };

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
        onBacktestComplete={handleBacktestComplete}
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
              {/* You can map a quick summary of backtests here if desired */}
            </tbody>
          </table>
        </div>
      </div>

      <h2 className="text-2xl font-bold text-gray-900">Backtest Results</h2>
      {plotUrl && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">Backtest Chart</h3>
          <img src={plotUrl} alt="Backtest Plot" className="border rounded shadow-lg max-w-full" />
        </div>
      )}

      {/* Scrollable table for all metrics */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-max text-sm text-left whitespace-nowrap">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2">Strategy Name</th>
              <th className="px-4 py-2">Ticker</th>
              <th className="px-4 py-2">Start Date</th>
              <th className="px-4 py-2">End Date</th>
              <th className="px-4 py-2">CAGR</th>
              <th className="px-4 py-2">Total Return %</th>
              <th className="px-4 py-2">Std Dev</th>
              <th className="px-4 py-2">Annual Vol</th>
              <th className="px-4 py-2">Sharpe Ratio</th>
              <th className="px-4 py-2">Sortino Ratio</th>
              <th className="px-4 py-2">Max Drawdown</th>
              <th className="px-4 py-2">Win Rate</th>
              <th className="px-4 py-2"># of Trades</th>
              <th className="px-4 py-2">Information Ratio</th>
              <th className="px-4 py-2">Strategy Unique ID</th>
            </tr>
          </thead>
          <tbody>
            {backtestResults.map((res, i) => (
              <tr key={i} className="border-t">
                <td className="px-4 py-2">{res.strategy_name}</td>
                <td className="px-4 py-2">{res.ticker}</td>
                <td className="px-4 py-2">{res.start_date}</td>
                <td className="px-4 py-2">{res.end_date}</td>
                <td className="px-4 py-2">{(res.cagr * 100).toFixed(2)}%</td>
                <td className="px-4 py-2">{res.total_return_pct.toFixed(2)}%</td>
                <td className="px-4 py-2">{res.std_dev !== null ? res.std_dev.toFixed(4) : 'N/A'}</td>
                <td className="px-4 py-2">{res.annual_vol !== null ? res.annual_vol.toFixed(4) : 'N/A'}</td>
                <td className="px-4 py-2">{res.sharpe_ratio !== null ? res.sharpe_ratio.toFixed(2) : 'N/A'}</td>
                <td className="px-4 py-2">{res.sortino_ratio !== null ? res.sortino_ratio.toFixed(2) : 'N/A'}</td>
                <td className="px-4 py-2">{res.max_drawdown !== null ? `${res.max_drawdown.toFixed(2)}%` : 'N/A'}</td>
                <td className="px-4 py-2">{res.win_rate !== null ? `${res.win_rate.toFixed(2)}%` : 'N/A'}</td>
                <td className="px-4 py-2">{res.num_trades !== null ? res.num_trades : 'N/A'}</td>
                <td className="px-4 py-2">{res.information_ratio !== null ? res.information_ratio.toFixed(2) : 'N/A'}</td>
                <td className="px-4 py-2">{res.strategy_unique_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Backtest;
