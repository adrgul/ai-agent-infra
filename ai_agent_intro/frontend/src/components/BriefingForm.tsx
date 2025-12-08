import { useState, FormEvent } from 'react';

interface BriefingFormProps {
  onSubmit: (city: string, date: string, language: string) => void;
  isLoading: boolean;
}

export function BriefingForm({ onSubmit, isLoading }: BriefingFormProps) {
  const [city, setCity] = useState('');
  const [date, setDate] = useState(() => {
    // Default to today
    return new Date().toISOString().split('T')[0];
  });
  const [language, setLanguage] = useState('en');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (city.trim()) {
      onSubmit(city.trim(), date, language);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">
        Get Weather Briefing
      </h2>
      
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-2">
            City
          </label>
          <input
            type="text"
            id="city"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="e.g., Budapest, London, Tokyo"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="date" className="block text-sm font-medium text-gray-700 mb-2">
            Date
          </label>
          <input
            type="date"
            id="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
            disabled={isLoading}
          />
        </div>

        <div className="md:col-span-2">
          <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-2">
            Language
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          >
            <option value="en">🇬🇧 English</option>
            <option value="es">🇪🇸 Spanish</option>
            <option value="fr">🇫🇷 French</option>
            <option value="de">🇩🇪 German</option>
            <option value="it">🇮🇹 Italian</option>
            <option value="pt">🇵🇹 Portuguese</option>
            <option value="nl">🇳🇱 Dutch</option>
            <option value="pl">🇵🇱 Polish</option>
            <option value="ru">🇷🇺 Russian</option>
            <option value="ja">🇯🇵 Japanese</option>
            <option value="zh">🇨🇳 Chinese</option>
            <option value="ko">🇰🇷 Korean</option>
            <option value="ar">🇸🇦 Arabic</option>
            <option value="hi">🇮🇳 Hindi</option>
            <option value="hu">🇭🇺 Hungarian</option>
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading || !city.trim()}
        className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? 'Loading...' : 'Get Briefing'}
      </button>
    </form>
  );
}
