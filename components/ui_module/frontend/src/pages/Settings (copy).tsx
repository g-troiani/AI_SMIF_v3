import React, { useState } from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const Settings: React.FC = () => {
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [environment, setEnvironment] = useState('paper');
  const [historicalPeriod, setHistoricalPeriod] = useState('5y');
  const [dataInterval, setDataInterval] = useState('5min');

  const handleSaveChanges = () => {
    // Implement save functionality
    console.log('Saving changes...');
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      console.log('File selected:', file.name);
    }
  };

  const handleDownloadTemplate = () => {
    // Implement template download
    console.log('Downloading template...');
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Data Settings</h2>
        <button
          onClick={handleSaveChanges}
          className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Save Changes
        </button>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">API Configuration</h3>
        <div className="space-y-4">
          <div>
            <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700">
              API Key
            </label>
            <input
              type="text"
              id="apiKey"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
            />
          </div>
          <div>
            <label htmlFor="apiSecret" className="block text-sm font-medium text-gray-700">
              API Secret
            </label>
            <input
              type="password"
              id="apiSecret"
              value={apiSecret}
              onChange={(e) => setApiSecret(e.target.value)}
              placeholder="Enter your API secret"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
            />
          </div>
          <div>
            <label htmlFor="environment" className="block text-sm font-medium text-gray-700">
              Environment
            </label>
            <select
              id="environment"
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
            >
              <option value="paper">Paper Trading</option>
              <option value="live">Live Trading</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-6">Data Settings</h3>
        <div className="space-y-4">
          <div>
            <label htmlFor="historicalPeriod" className="block text-sm font-medium text-gray-700">
              Historical Data Period
            </label>
            <select
              id="historicalPeriod"
              value={historicalPeriod}
              onChange={(e) => setHistoricalPeriod(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
            >
              <option value="5y">5 Years</option>
            </select>
          </div>
          <div>
            <label htmlFor="dataInterval" className="block text-sm font-medium text-gray-700">
              Data Interval
            </label>
            <select
              id="dataInterval"
              value={dataInterval}
              onChange={(e) => setDataInterval(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
            >
              <option value="5min">5 Minutes</option>
            </select>
          </div>
          <div>
            <label htmlFor="tickersFile" className="block text-sm font-medium text-gray-700">
              Tickers File
            </label>
            <div className="mt-1 flex items-center">
              <label className="relative flex-1">
                <input
                  type="file"
                  id="tickersFile"
                  onChange={handleFileUpload}
                  className="sr-only"
                  accept=".csv"
                />
                <div className="flex items-center justify-between px-4 py-2 border border-gray-300 rounded-md bg-white text-sm text-gray-700 hover:bg-gray-100 cursor-pointer">
                  <span>Choose File</span>
                </div>
              </label>
              <button
                onClick={handleDownloadTemplate}
                className="ml-4 text-indigo-600 hover:text-indigo-700 text-sm"
              >
                Download Template
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-md bg-yellow-50 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" aria-hidden="true" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              Changing these settings will require a full data resync. This process may take several minutes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;