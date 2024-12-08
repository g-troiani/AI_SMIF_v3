import React, { useState } from 'react';
import NewStrategyModal from '../components/NewStrategyModal';

const Strategy: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenModal = () => {
    console.log('Opening modal, current state:', isModalOpen);
    setIsModalOpen(true);
    console.log('State after setting:', true);
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

      <div className="hidden">Modal state: {isModalOpen ? 'open' : 'closed'}</div>

      <NewStrategyModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />

      <div className="bg-white shadow rounded-lg">
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Available Strategies</h3>
          <div className="text-gray-500">No strategies configured</div>
        </div>
      </div>
    </div>
  );
};

export default Strategy;