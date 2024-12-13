import { useState, useEffect } from 'react';

interface PortfolioData {
  history: Array<{
    date: string;
    value: number;
  }>;
  currentBalance: number;
  percentageChange: number;
}

export const usePortfolioData = (timeFilter: string) => {
  const [data, setData] = useState<PortfolioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/api/portfolio/history?period=${timeFilter}`);
        const result = await response.json();
        
        if (result.success && result.data) {
          const validData = {
            ...result.data,
            history: result.data.history
              .filter((point: any) => 
                typeof point.value === 'number' && 
                !isNaN(point.value) && 
                point.value > 0
              )
              .map((point: any) => ({
                date: point.date,
                value: Number(point.value)
              }))
          };
          setData(validData);
          setError(null);
        } else {
          setError(result.message || 'Failed to fetch portfolio data');
        }
      } catch (error) {
        setError('Error fetching portfolio data');
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [timeFilter]);

  return { data, loading, error };
};