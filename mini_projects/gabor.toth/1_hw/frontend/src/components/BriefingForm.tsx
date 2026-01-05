import { useState } from "react";

interface BriefingFormProps {
  onSubmit: (params: {
    city: string;
    activity?: string;
  }) => void;
  isLoading?: boolean;
}

export const BriefingForm = ({ onSubmit, isLoading = false }: BriefingFormProps) => {
  const [city, setCity] = useState("");
  const [activity, setActivity] = useState("");
  const [isShuttingDown, setIsShuttingDown] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (city.trim()) {
      onSubmit({
        city: city.trim(),
        activity: activity.trim() || undefined,
      });
    }
  };

  const handleShutdown = async () => {
    if (window.confirm("Valóban szeretnéd leállítani az alkalmazást?")) {
      setIsShuttingDown(true);
      try {
        await fetch("http://localhost:3000/api/shutdown", { method: "POST" });
        setTimeout(() => {
          window.close();
        }, 1000);
      } catch (error) {
        console.error("Shutdown error:", error);
        setIsShuttingDown(false);
      }
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded-lg shadow">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Város
        </label>
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="pl. Budapest, Párizs, Tokió"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Mit szeretnél csinálni?
        </label>
        <input
          type="text"
          value={activity}
          onChange={(e) => setActivity(e.target.value)}
          placeholder="pl. túrázás, múzeumok, kávézók, éjszakai élet"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
      </div>

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={isLoading || !city.trim()}
          className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-md transition-colors"
        >
          {isLoading ? "Tájékoztató készítése..." : "Tájékoztató Készítése"}
        </button>
        
        <button
          type="button"
          onClick={handleShutdown}
          disabled={isShuttingDown}
          className="bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-md transition-colors min-w-fit"
        >
          {isShuttingDown ? "Leállítás..." : "🛑 Bezárás"}
        </button>
      </div>
    </form>
  );
};
