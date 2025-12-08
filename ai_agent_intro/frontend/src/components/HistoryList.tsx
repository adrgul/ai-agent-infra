import { useQuery } from '@tanstack/react-query';
import { getHistory } from '../api/client';
import type { HistoryEntry } from '../types';

export function HistoryList() {
  const { data: history, isLoading } = useQuery<HistoryEntry[]>({
    queryKey: ['history'],
    queryFn: getHistory,
    staleTime: 30 * 1000, // 30 seconds
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Searches</h3>
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (!history || history.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Searches</h3>
        <p className="text-gray-600">No history yet</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Recent Searches</h3>
      <div className="space-y-2">
        {history.map((entry, index) => (
          <div
            key={index}
            className="flex justify-between items-center py-2 border-b border-gray-200 last:border-0"
          >
            <div>
              <p className="font-medium text-gray-800">{entry.city}</p>
              <p className="text-sm text-gray-600">
                {new Date(entry.date).toLocaleDateString()}
              </p>
            </div>
            <p className="text-xs text-gray-500">
              {new Date(entry.timestamp).toLocaleTimeString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
