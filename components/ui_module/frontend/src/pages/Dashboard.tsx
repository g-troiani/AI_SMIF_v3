import DashboardMetrics from '../components/dashboard/DashboardMetrics';
import DashboardChart from '../components/dashboard/DashboardChart';
import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';


const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <DashboardMetrics />
      
      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Portfolio Performance Chart */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-6">
            <h3 className="text-lg font-medium leading-6 text-gray-900">
              Portfolio Performance
            </h3>
            <div className="mt-5">
              <DashboardChart />
            </div>
          </div>
        </div>

        {/* Other components */}
      </div>
    </div>
  );
};

export default Dashboard;
