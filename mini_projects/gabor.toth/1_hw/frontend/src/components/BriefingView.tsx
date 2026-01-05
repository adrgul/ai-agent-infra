import { CityBriefingResponse } from "../api/types";
import { BriefingCards } from "./Cards";

interface BriefingViewProps {
  data: CityBriefingResponse;
}

export const BriefingView = ({ data }: BriefingViewProps) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-8 rounded-lg">
        <h1 className="text-4xl font-bold mb-2">{data.city}</h1>
        <p className="text-blue-200 mt-2">
          Coordinates: {data.coordinates.lat.toFixed(4)}, {data.coordinates.lon.toFixed(4)}
        </p>
      </div>

      {/* Main Briefing */}
      <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-600">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Wikipedia összefoglaló a tevékenységre vonatkozóan</h2>
        <p className="text-gray-700 leading-relaxed text-lg">{data.briefing.paragraph}</p>
      </div>

      {/* Cards Section */}
      <BriefingCards data={data} />

      {/* Közeli Helyek - Google Maps Linkekkel */}
      {data.nearby_places && data.nearby_places.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          {/* Fallback üzenet, ha van */}
          {data.fallback_message && (
            <div className="mb-4 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded">
              <p className="text-yellow-800 text-sm font-medium">{data.fallback_message}</p>
            </div>
          )}
          
          <h3 className="text-xl font-bold text-gray-800 mb-4">📍 Közeli Helyek</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.nearby_places.map((place, idx) => (
              <a
                key={idx}
                href={`https://maps.google.com/?q=${place.lat},${place.lon}`}
                target="_blank"
                rel="noopener noreferrer"
                className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg border border-blue-200 hover:shadow-lg hover:border-blue-400 transition-all cursor-pointer"
              >
                <h4 className="font-semibold text-blue-800">{place.name}</h4>
                <p className="text-sm text-blue-700 mt-2">
                  📌 {place.distance_m > 1000 ? `${(place.distance_m / 1000).toFixed(1)} km` : `${place.distance_m} m`} away
                </p>
                <p className="text-xs text-blue-600 mt-1">🚶 ~{place.walking_minutes} perc gyalogosan</p>
                <span className="inline-block mt-2 px-2 py-1 bg-blue-200 text-blue-800 text-xs rounded-full">
                  {place.type}
                </span>
                <p className="text-xs text-blue-500 mt-2 font-semibold">🗺️ Nyissa meg a Google Maps-ban</p>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Ajánlott Tevékenységek - csak a koordináták kellenek */}
    </div>
  );
};
