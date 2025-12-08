import type { BriefingResponse } from '../types';

interface BriefingCardProps {
  data: BriefingResponse;
}

export function BriefingCard({ data }: BriefingCardProps) {
  const { city, country, date, weather, briefing } = data;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      {/* Header */}
      <div className="border-b pb-4 mb-4">
        <h3 className="text-2xl font-bold text-gray-800">
          {city}, {country}
        </h3>
        <p className="text-gray-600">{new Date(date).toLocaleDateString()}</p>
      </div>

      {/* Weather Info */}
      <div className="bg-blue-50 rounded-lg p-4 mb-4">
        <h4 className="font-semibold text-gray-700 mb-2">Weather Forecast</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-600">Min Temp</p>
            <p className="font-semibold text-lg">{weather.temperature_min}°C</p>
          </div>
          <div>
            <p className="text-gray-600">Max Temp</p>
            <p className="font-semibold text-lg">{weather.temperature_max}°C</p>
          </div>
          <div>
            <p className="text-gray-600">Wind</p>
            <p className="font-semibold text-lg">{weather.wind_speed} m/s</p>
          </div>
          <div>
            <p className="text-gray-600">Rain</p>
            <p className="font-semibold text-lg">{weather.precipitation_probability}%</p>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="mb-4">
        <h4 className="font-semibold text-gray-700 mb-2">Summary</h4>
        <p className="text-gray-800">{briefing.summary}</p>
      </div>

      {/* Outfit */}
      <div className="mb-4">
        <h4 className="font-semibold text-gray-700 mb-2">👔 What to Wear</h4>
        <p className="text-gray-800">{briefing.outfit}</p>
      </div>

      {/* Activities */}
      <div className="mb-4">
        <h4 className="font-semibold text-gray-700 mb-2">🎯 Activity Suggestions</h4>
        <ul className="space-y-2">
          {briefing.activities.map((activity, index) => (
            <li key={index} className="flex items-start">
              <span className="text-blue-600 mr-2">•</span>
              <span className="text-gray-800">{activity}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Note */}
      {briefing.note && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mt-4">
          <p className="text-sm text-yellow-800">
            <span className="font-semibold">Note:</span> {briefing.note}
          </p>
        </div>
      )}
    </div>
  );
}
