import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import { Dashboard, Strategy, Backtest, Portfolio, DataManagement, Settings } from './pages';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="strategy" element={<Strategy />} />
        <Route path="backtest" element={<Backtest />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="data" element={<DataManagement />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;