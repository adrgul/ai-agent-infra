import { CityBriefingResponse } from "../api/types";

interface BriefingCardsProps {
  data: CityBriefingResponse;
}

export const BriefingCards = ({ data }: BriefingCardsProps) => {
  return (
    <div className="space-y-6">
      {/* City Facts */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Wikipedia releváns információk a településre vonatkozóan</h3>
        <div className="space-y-4">
          {data.city_facts.map((fact, idx) => (
            <div key={idx} className="p-4 bg-purple-50 rounded-lg border-l-4 border-purple-500">
              <h4 className="font-semibold text-purple-900 mb-2">{fact.title}</h4>
              <p className="text-sm text-purple-800">{fact.content}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
