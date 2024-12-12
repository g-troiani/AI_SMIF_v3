// File: components/ui_module/frontend/src/pages/Dashboard.tsx

import DashboardMetrics from '../components/dashboard/DashboardMetrics';
import DashboardChart from '../components/dashboard/DashboardChart';
import MarketOverview from '../components/dashboard/MarketOverview';
import React from 'react';

const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <DashboardMetrics />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio Performance Card */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-sm font-medium text-gray-500">Portfolio Performance</h3>
          <DashboardChart />
        </div>

        {/* Market Overview */}
        <MarketOverview />
      </div>
    </div>
  );
};

export default Dashboard;
