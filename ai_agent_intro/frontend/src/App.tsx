import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BriefingForm } from './components/BriefingForm';
import { BriefingCard } from './components/BriefingCard';
import { HistoryList } from './components/HistoryList';
import ProfileSettings from './components/ProfileSettings';
import { useBriefing } from './hooks/useBriefing';
import type { BriefingRequest } from './types';
import './styles.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

function BriefingApp() {
  const [request, setRequest] = useState<BriefingRequest | null>(null);
  const [showProfile, setShowProfile] = useState(false);
  const { data, isLoading, error } = useBriefing(request);

  const handleFormSubmit = (city: string, date: string, language: string) => {
    setRequest({ city, date, language });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <header className="text-center mb-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex-1"></div>
            <h1 className="text-4xl font-bold text-gray-800 flex-1">
              ☁️ AI Weather Agent
            </h1>
            <div className="flex-1 flex justify-end">
              <button
                onClick={() => setShowProfile(true)}
                className="px-4 py-2 bg-white text-gray-700 rounded-lg shadow hover:shadow-md transition-shadow flex items-center space-x-2"
                title="Configure your profile for personalized recommendations"
              >
                <span>👤</span>
                <span className="hidden sm:inline">Profile</span>
              </button>
            </div>
          </div>
          <p className="text-gray-600">
            Get personalized weather briefings with outfit tips and activity suggestions
          </p>
        </header>

        {/* Profile Modal */}
        {showProfile && <ProfileSettings onClose={() => setShowProfile(false)} />}

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <BriefingForm onSubmit={handleFormSubmit} isLoading={isLoading} />

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6 rounded">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <span className="text-red-400 text-xl">⚠️</span>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <p className="text-sm text-red-700 mt-1">
                      {error instanceof Error ? error.message : 'An error occurred'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {isLoading && (
              <div className="bg-white rounded-lg shadow-md p-8 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Generating your briefing...</p>
              </div>
            )}

            {/* Success State */}
            {data && !isLoading && <BriefingCard data={data} />}

            {/* Empty State */}
            {!data && !isLoading && !error && (
              <div className="bg-white rounded-lg shadow-md p-8 text-center">
                <p className="text-gray-600">
                  Enter a city and date above to get started
                </p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <HistoryList />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-gray-600">
          <p>
            Powered by{' '}
            <a
              href="https://openai.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              OpenAI
            </a>
            ,{' '}
            <a
              href="https://open-meteo.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              Open-Meteo
            </a>
            , and{' '}
            <a
              href="https://nominatim.openstreetmap.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              OpenStreetMap
            </a>
          </p>
        </footer>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BriefingApp />
    </QueryClientProvider>
  );
}

export default App;
