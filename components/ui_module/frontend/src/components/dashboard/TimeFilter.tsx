import React from 'react';

type TimeFilterOption = '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL';

interface TimeFilterProps {
  selected: TimeFilterOption;
  onChange: (filter: TimeFilterOption) => void;
}

const TimeFilter: React.FC<TimeFilterProps> = ({ selected, onChange }) => {
  const options: TimeFilterOption[] = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];

  return (
    <div className="flex space-x-2">
      {options.map((period) => (
        <button
          key={period}
          onClick={() => onChange(period)}
          className={`px-3 py-1 text-sm rounded-full transition-colors ${
            selected === period 
              ? 'bg-green-600 text-white' 
              : 'text-gray-600 hover:bg-gray-100'
          }`}
        >
          {period}
        </button>
      ))}
    </div>
  );
};

export default TimeFilter;