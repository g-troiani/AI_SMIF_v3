// import { useState, useEffect } from 'react';

// const MarketOverview = () => {
//   const [marketData, setMarketData] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);

//   useEffect(() => {
//     const fetchMarketData = async () => {
//       try {
//         const response = await fetch('/api/market-overview');
//         const result = await response.json();
        
//         if (result.success) {
//           setMarketData(result.data);
//         } else {
//           setError(result.message);
//         }
//       } catch (err) {
//         setError('Failed to fetch market data');
//       } finally {
//         setLoading(false);
//       }
//     };

//     fetchMarketData();
//     const interval = setInterval(fetchMarketData, 60000); // Update every minute
    
//     return () => clearInterval(interval);
//   }, []);

//   if (loading) {
//     return (
//       <div className="bg-white p-6 rounded-lg shadow-lg">
//         <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
//         <div className="flex items-center justify-center h-40">
//           <p className="text-gray-500">Loading market data...</p>
//         </div>
//       </div>
//     );
//   }

//   if (error) {
//     return (
//       <div className="bg-white p-6 rounded-lg shadow-lg">
//         <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
//         <div className="text-red-500">
//           {error}
//         </div>
//       </div>
//     );
//   }

//   return (
//     <div className="bg-white p-6 rounded-lg shadow-lg">
//       <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
//       <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
//         {marketData.map((item) => (
//           <div
//             key={item.symbol}
//             className="flex items-center justify-between p-4 rounded-lg bg-gray-50"
//           >
//             <div>
//               <h3 className="text-sm text-gray-600">{item.name}</h3>
//               <p className="text-2xl font-bold">
//                 ${item.price.toLocaleString(undefined, {
//                   minimumFractionDigits: 2,
//                   maximumFractionDigits: 2,
//                 })}
//               </p>
//             </div>
//             <div className={`flex items-center ${
//               item.change >= 0 ? 'text-green-500' : 'text-red-500'
//             }`}>
//               <span className="mr-1">
//                 {item.change >= 0 ? '▲' : '▼'}
//               </span>
//               <span className="font-medium">
//                 {Math.abs(item.change).toFixed(2)}%
//               </span>
//             </div>
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// };

// export default MarketOverview;