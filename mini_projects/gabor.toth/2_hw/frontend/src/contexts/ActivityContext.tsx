import React, { createContext, useContext, useState, useCallback } from 'react';

export interface LogEntry {
  id: string;
  timestamp: number;  // Change from string to number (milliseconds)
  message: string;
  type: 'info' | 'success' | 'error' | 'warning' | 'processing';
}

interface ActivityContextType {
  entries: LogEntry[];
  addActivity: (message: string, type?: LogEntry['type']) => string;
  updateActivity: (id: string, message: string, type?: LogEntry['type']) => void;
  clearActivities: () => void;
  removeActivity: (id: string) => void;
}

const ActivityContext = createContext<ActivityContextType | undefined>(undefined);

export const ActivityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [entries, setEntries] = useState<LogEntry[]>([]);

  const addActivity = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    const timestamp = Date.now();  // Use milliseconds like backend
    const newEntry: LogEntry = { id, timestamp, message, type };
    
    setEntries(prev => [newEntry, ...prev]);
    return id;
  }, []);

  const updateActivity = useCallback((id: string, message: string, type: LogEntry['type'] = 'info') => {
    setEntries(prev =>
      prev.map(entry =>
        entry.id === id
          ? { ...entry, message, type, timestamp: Date.now() }  // Use milliseconds
          : entry
      )
    );
  }, []);

  const clearActivities = useCallback(() => {
    setEntries([]);
  }, []);

  const removeActivity = useCallback((id: string) => {
    setEntries(prev => prev.filter(entry => entry.id !== id));
  }, []);

  return (
    <ActivityContext.Provider value={{ entries, addActivity, updateActivity, clearActivities, removeActivity }}>
      {children}
    </ActivityContext.Provider>
  );
};

export const useActivity = (): ActivityContextType => {
  const context = useContext(ActivityContext);
  if (!context) {
    throw new Error('useActivity must be used within ActivityProvider');
  }
  return context;
};
