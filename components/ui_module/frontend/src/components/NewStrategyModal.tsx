import React, { useState } from 'react';
import { XMarkIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

interface TradingRule {
  indicator: string;
  operator: string;
  value: string;
  logicalOperator: string;
  action: string;
}

interface StrategyFormData {
  name: string;
  description: string;
  rules: TradingRule[];
  stopLoss: number;
  takeProfit: number;
}

interface NewStrategyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NewStrategyModal: React.FC<NewStrategyModalProps> = ({ isOpen, onClose }) => {
  const [formData, setFormData] = useState<StrategyFormData>({
    name: '',
    description: '',
    rules: [{
      indicator: 'Price',
      operator: 'Greater Than',
      value: '0',
      logicalOperator: 'AND',
      action: 'Buy'
    }],
    stopLoss: 2,
    takeProfit: 5
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/strategies', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      if (response.ok) {
        onClose();
      }
    } catch (error) {
      console.error('Error creating strategy:', error);
    }
  };

  const addRule = () => {
    setFormData(prev => ({
      ...prev,
      rules: [...prev.rules, {
        indicator: 'Price',
        operator: 'Greater Than',
        value: '0',
        logicalOperator: 'AND',
        action: 'Buy'
      }]
    }));
  };

  const removeRule = (index: number) => {
    setFormData(prev => ({
      ...prev,
      rules: prev.rules.filter((_, i) => i !== index)
    }));
  };

  const updateRule = (index: number, field: keyof TradingRule, value: string) => {
    setFormData(prev => ({
      ...prev,
      rules: prev.rules.map((rule, i) => 
        i === index ? { ...rule, [field]: value } : rule
      )
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">New Strategy</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-500">
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Strategy Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">
              Strategy Name
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              rows={3}
              value={formData.description}
              onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
          </div>

          {/* Trading Rules */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Trading Rules</h3>
              <button
                type="button"
                onClick={addRule}
                className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-indigo-600 hover:text-indigo-500"
              >
                <PlusIcon className="h-5 w-5 mr-1" />
                Add Rule
              </button>
            </div>

            <div className="space-y-4">
              {formData.rules.map((rule, index) => (
                <div key={index} className="flex items-start space-x-4 bg-gray-50 p-4 rounded-md">
                  <div className="flex-grow grid grid-cols-5 gap-4">
                    <select
                      value={rule.indicator}
                      onChange={e => updateRule(index, 'indicator', e.target.value)}
                      className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                      <option>Price</option>
                      <option>Volume</option>
                      <option>RSI</option>
                      <option>MACD</option>
                    </select>
                    <select
                      value={rule.operator}
                      onChange={e => updateRule(index, 'operator', e.target.value)}
                      className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                      <option>Greater Than</option>
                      <option>Less Than</option>
                      <option>Equals</option>
                    </select>
                    <input
                      type="text"
                      value={rule.value}
                      onChange={e => updateRule(index, 'value', e.target.value)}
                      className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                    <select
                      value={rule.logicalOperator}
                      onChange={e => updateRule(index, 'logicalOperator', e.target.value)}
                      className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                      <option>AND</option>
                      <option>OR</option>
                    </select>
                    <select
                      value={rule.action}
                      onChange={e => updateRule(index, 'action', e.target.value)}
                      className="rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    >
                      <option>Buy</option>
                      <option>Sell</option>
                    </select>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeRule(index)}
                    className="text-red-500 hover:text-red-600"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Risk Management */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Risk Management</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="stopLoss" className="block text-sm font-medium text-gray-700">
                  Stop Loss (%)
                </label>
                <input
                  type="number"
                  id="stopLoss"
                  value={formData.stopLoss}
                  onChange={e => setFormData(prev => ({ ...prev, stopLoss: Number(e.target.value) }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label htmlFor="takeProfit" className="block text-sm font-medium text-gray-700">
                  Take Profit (%)
                </label>
                <input
                  type="number"
                  id="takeProfit"
                  value={formData.takeProfit}
                  onChange={e => setFormData(prev => ({ ...prev, takeProfit: Number(e.target.value) }))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Save Strategy
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewStrategyModal;